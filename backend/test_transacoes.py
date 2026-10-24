"""Atomicidade de criação, realização e carga inicial em bancos isolados."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    Agendamento, LancamentoFinanceiro, Paciente, PerfilUsuario, Psicologo,
    StatusAgendamento, TipoLancamento, Usuario,
)
from app.routers.agendamentos import criar_agendamento
from app.routers.prontuario import criar_evolucao
from app.schemas import AgendamentoCreate, ProntuarioCreate
from app.seed import seed_database
from app.services import aplicar_status_agendamento


class TransacoesTest(unittest.TestCase):
    def setUp(self):
        self.relogio = patch("app.horarios.agora_utc", return_value=datetime(2026, 10, 22))
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.paciente = Paciente(nome="Paciente fictício")
        self.psi = Psicologo(nome="Profissional fictício", crp="teste", email="psi@example.com",
                            percentual_repasse=60)
        self.user = Usuario(nome="Gestão", email="gestao@example.com", senha_hash="nao-utilizado",
                            perfil=PerfilUsuario.admin)
        self.db.add_all([self.paciente, self.psi, self.user])
        self.db.commit()
        self.inicio = datetime(2026, 10, 23, 14)
        self.fim = self.inicio + timedelta(minutes=50)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def falhar_durante_faturamento(self, db, ag):
        db.add(LancamentoFinanceiro(agendamento_id=ag.id, psicologo_id=self.psi.id,
                                    descricao="Lançamento parcial fictício", tipo=TipoLancamento.receita,
                                    valor=220, automatico=True))
        db.flush()
        raise RuntimeError("Falha simulada após escrita parcial")

    def test_falha_financeira_nao_persiste_status_realizado(self):
        ag = Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                         inicio=self.inicio, fim=self.fim)
        self.db.add(ag)
        self.db.commit()
        with patch("app.services.criar_lancamentos_agendamento_realizado", self.falhar_durante_faturamento):
            with self.assertRaises(RuntimeError):
                aplicar_status_agendamento(self.db, ag, StatusAgendamento.realizado)
        self.db.refresh(ag)
        self.assertEqual(ag.status, StatusAgendamento.agendado)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 0)

    def test_falha_financeira_na_criacao_nao_deixa_agendamento(self):
        payload = AgendamentoCreate(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                                    inicio=self.inicio, fim=self.fim, status="realizado")
        with patch("app.services.criar_lancamentos_agendamento_realizado", self.falhar_durante_faturamento):
            with self.assertRaises(RuntimeError):
                criar_agendamento(payload, self.db, self.user)
        self.assertEqual(self.db.query(Agendamento).count(), 0)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 0)

    def test_realizacao_tem_um_unico_commit(self):
        ag = Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                         inicio=self.inicio, fim=self.fim)
        self.db.add(ag)
        self.db.commit()
        with patch.object(self.db, "commit", wraps=self.db.commit) as commit:
            aplicar_status_agendamento(self.db, ag, StatusAgendamento.realizado)
        self.assertEqual(commit.call_count, 1)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)

    def test_criacao_realizada_tem_um_unico_commit(self):
        payload = AgendamentoCreate(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                                    inicio=self.inicio, fim=self.fim, status="realizado")
        with patch.object(self.db, "commit", wraps=self.db.commit) as commit:
            resposta = criar_agendamento(payload, self.db, self.user)
        self.assertEqual(commit.call_count, 1)
        self.assertEqual(resposta.status, StatusAgendamento.realizado)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)

    def test_falha_na_evolucao_reverte_registro_e_libera_atendimento(self):
        from app.models import Prontuario
        ag = Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                         inicio=self.inicio, fim=self.fim)
        self.db.add(ag)
        self.db.commit()
        aplicar_status_agendamento(self.db, ag, StatusAgendamento.realizado)
        self.user.psicologo_id = self.psi.id
        self.db.commit()

        def falhar_apos_flush():
            self.db.flush()
            raise RuntimeError("Falha simulada após gravar evolução na transação")

        with patch.object(self.db, "commit", side_effect=falhar_apos_flush):
            with self.assertRaises(RuntimeError):
                criar_evolucao(ProntuarioCreate(agendamento_id=ag.id, evolucao="Evolução fictícia"), self.db, self.user)
        self.assertEqual(self.db.query(Prontuario).count(), 0)
        self.assertEqual(self.db.get(Agendamento, ag.id).status, StatusAgendamento.realizado)
        # Uma nova tentativa usa a sessão recuperada, sem registro parcial.
        criar_evolucao(ProntuarioCreate(agendamento_id=ag.id, evolucao="Evolução fictícia"), self.db, self.user)
        self.assertEqual(self.db.query(Prontuario).count(), 1)

    def test_seed_nao_persiste_parcialmente_se_faturamento_falhar(self):
        engine_vazio = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine_vazio)
        try:
            with Session(engine_vazio) as db:
                with patch("app.services.criar_lancamentos_agendamento_realizado", side_effect=RuntimeError("Falha simulada")):
                    with self.assertRaises(RuntimeError):
                        seed_database(db)
                db.rollback()
                self.assertEqual(db.query(Usuario).count(), 0)
                self.assertEqual(db.query(Agendamento).count(), 0)
                self.assertEqual(db.query(LancamentoFinanceiro).count(), 0)
        finally:
            engine_vazio.dispose()


if __name__ == "__main__":
    unittest.main()
