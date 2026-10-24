"""Horários vencidos e reagendamento rastreável, com relógio controlado."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Agendamento, LancamentoFinanceiro, Paciente, PerfilUsuario, Prontuario, Psicologo, StatusAgendamento, Usuario
from app.routers.agendamentos import _serialize, atualizar_agendamento, criar_agendamento
from app.schemas import AgendamentoCreate, AgendamentoUpdate


class ReagendamentoTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False)
        self.agora = datetime(2026, 10, 23, 12)
        self.relogio = patch("app.horarios.agora_utc", return_value=self.agora)
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.paciente = Paciente(nome="Paciente fictício")
        self.psi = Psicologo(nome="Profissional fictício", crp="teste", email="psi@example.com")
        self.user = Usuario(nome="Gestão fictícia", email="gestao@example.com", senha_hash="nao-utilizado", perfil=PerfilUsuario.admin)
        self.db.add_all([self.paciente, self.psi, self.user])
        self.db.flush()
        self.origem = Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                                  inicio=datetime(2026, 10, 22, 22), fim=datetime(2026, 10, 22, 22, 50),
                                  criado_em=datetime(2026, 10, 15, 12), status=StatusAgendamento.cancelado)
        self.db.add(self.origem)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def afirmar_recusa(self, codigo, acao):
        with self.assertRaises(HTTPException) as erro:
            acao()
        self.assertEqual(erro.exception.status_code, codigo)

    def atualizar(self, **dados):
        return atualizar_agendamento(self.origem.id, AgendamentoUpdate(**dados), self.db, self.user)

    def reagendar(self, inicio=None, fim=None):
        from app.routers.agendamentos import reagendar_agendamento
        from app.schemas import ReagendamentoCreate
        inicio = inicio if inicio is not None else self.agora + timedelta(days=1)
        fim = fim if fim is not None else inicio + timedelta(minutes=50)
        return reagendar_agendamento(self.origem.id, ReagendamentoCreate(inicio=inicio, fim=fim), self.db, self.user)

    def test_novo_agendamento_recusa_passado_e_instante_atual(self):
        for inicio in [self.agora - timedelta(minutes=1), self.agora]:
            with self.subTest(inicio=inicio):
                payload = AgendamentoCreate(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                                            inicio=inicio, fim=inicio + timedelta(minutes=50))
                self.afirmar_recusa(422, lambda: criar_agendamento(payload, self.db, self.user))
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_exemplo_do_usuario_nao_reabre_horario_vencido(self):
        self.afirmar_recusa(409, lambda: self.atualizar(status="agendado"))
        self.assertEqual(self.origem.status, StatusAgendamento.cancelado)

    def test_patch_nao_reabre_original_vencido_trocando_a_data(self):
        self.afirmar_recusa(409, lambda: self.atualizar(status="agendado", inicio=self.agora + timedelta(days=1), fim=self.agora + timedelta(days=1, minutes=50)))
        self.assertEqual(self.origem.inicio, datetime(2026, 10, 22, 22))

    def test_nao_confirma_agendamento_cujo_inicio_ja_passou(self):
        self.origem.status = StatusAgendamento.agendado
        self.db.commit()
        self.afirmar_recusa(409, lambda: self.atualizar(status="confirmado"))

    def test_realizacao_tardia_continua_permitida(self):
        self.origem.status = StatusAgendamento.agendado
        self.db.commit()
        self.atualizar(status="realizado")
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)

    def test_cancelamento_e_manutencao_textual_tardios_continuam_permitidos(self):
        self.origem.status = StatusAgendamento.agendado
        self.db.commit()
        self.atualizar(status="cancelado")
        self.atualizar(observacoes="Manutenção administrativa")
        self.assertEqual(self.origem.status, StatusAgendamento.cancelado)

    def test_reabertura_futura_sem_historico_continua_permitida(self):
        self.origem.inicio = self.agora + timedelta(days=1)
        self.origem.fim = self.origem.inicio + timedelta(minutes=50)
        self.db.commit()
        self.atualizar(status="agendado")
        self.assertEqual(self.origem.status, StatusAgendamento.agendado)

    def test_reagendamento_cria_novo_e_preserva_cancelado_original(self):
        novo = self.reagendar()
        from app.models import Reagendamento
        self.assertNotEqual(novo.id, self.origem.id)
        self.assertEqual(self.db.query(Agendamento).count(), 2)
        self.db.refresh(self.origem)
        self.assertEqual(self.origem.status, StatusAgendamento.cancelado)
        self.assertEqual(self.origem.inicio, datetime(2026, 10, 22, 22))
        self.assertEqual(self.origem.criado_em, datetime(2026, 10, 15, 12))
        vinculo = self.db.query(Reagendamento).one()
        self.assertEqual((vinculo.agendamento_original_id, vinculo.novo_agendamento_id, vinculo.usuario_id),
                         (self.origem.id, novo.id, self.user.id))
        self.assertEqual(novo.reagendado_de_id, self.origem.id)

    def test_reagendamento_recusa_data_passada_e_nao_cria_registro(self):
        self.afirmar_recusa(422, lambda: self.reagendar(inicio=self.agora - timedelta(days=1)))
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_original_so_pode_gerar_um_sucessor(self):
        self.reagendar()
        self.afirmar_recusa(409, lambda: self.reagendar(inicio=self.agora + timedelta(days=2)))
        self.assertEqual(self.db.query(Agendamento).count(), 2)

    def test_reagendamento_bloqueado_quando_ha_financeiro(self):
        self.db.add(LancamentoFinanceiro(agendamento_id=self.origem.id, psicologo_id=self.psi.id,
                                         descricao="Histórico fictício", valor=220, automatico=True))
        self.db.commit()
        self.afirmar_recusa(409, self.reagendar)

    def test_reagendamento_bloqueado_quando_ha_prontuario(self):
        self.db.add(Prontuario(agendamento_id=self.origem.id, psicologo_id=self.psi.id,
                              paciente_id=self.paciente.id, evolucao="Evolução fictícia"))
        self.db.commit()
        self.afirmar_recusa(409, self.reagendar)

    def test_reagendamento_conflictante_nao_muda_origem(self):
        self.db.add(Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                                inicio=self.agora + timedelta(days=1), fim=self.agora + timedelta(days=1, minutes=50)))
        self.db.commit()
        self.afirmar_recusa(409, self.reagendar)
        self.assertEqual(self.origem.status, StatusAgendamento.cancelado)
        self.assertEqual(self.db.query(Agendamento).count(), 2)

    def test_acoes_disponiveis_distinguem_reabrir_de_reagendar(self):
        resposta = _serialize(self.origem)
        self.assertFalse(resposta.pode_reabrir)
        self.assertTrue(resposta.pode_reagendar)

    def test_falha_ao_gravar_reagendamento_reverte_todos_os_efeitos(self):
        from app.models import Reagendamento
        self.origem.status = StatusAgendamento.confirmado
        self.db.commit()

        def falhar_apos_flush():
            self.db.flush()
            raise RuntimeError("Falha simulada após escrita do vínculo")

        with patch.object(self.db, "commit", side_effect=falhar_apos_flush):
            with self.assertRaises(RuntimeError):
                self.reagendar()
        self.db.refresh(self.origem)
        self.assertEqual(self.origem.status, StatusAgendamento.confirmado)
        self.assertEqual(self.db.query(Agendamento).count(), 1)
        self.assertEqual(self.db.query(Reagendamento).count(), 0)

    def test_reagendar_reserva_aberta_cancela_original_sem_mudar_sua_data(self):
        self.origem.status = StatusAgendamento.agendado
        self.db.commit()
        novo = self.reagendar()
        self.db.refresh(self.origem)
        self.assertEqual(self.origem.status, StatusAgendamento.cancelado)
        self.assertEqual(self.origem.inicio, datetime(2026, 10, 22, 22))
        self.assertEqual(novo.status, StatusAgendamento.agendado)

    def test_reagendar_falta_preserva_status_de_falta(self):
        self.origem.status = StatusAgendamento.falta
        self.db.commit()
        self.reagendar()
        self.db.refresh(self.origem)
        self.assertEqual(self.origem.status, StatusAgendamento.falta)

    def test_realizado_nao_pode_ser_reagendado(self):
        self.origem.status = StatusAgendamento.realizado
        self.db.commit()
        self.afirmar_recusa(409, self.reagendar)

    def test_psicologo_nao_reagenda_atendimento_de_outro_profissional(self):
        outro = Psicologo(nome="Outro fictício", crp="outro", email="outro@example.com")
        self.db.add(outro)
        self.db.flush()
        self.user.perfil = PerfilUsuario.psicologo
        self.user.psicologo_id = outro.id
        self.db.commit()
        self.afirmar_recusa(403, self.reagendar)

    def test_original_futuro_ja_reagendado_nao_pode_reabrir(self):
        self.origem.inicio = self.agora + timedelta(hours=2)
        self.origem.fim = self.origem.inicio + timedelta(minutes=50)
        self.db.commit()
        self.reagendar()
        self.afirmar_recusa(409, lambda: self.atualizar(status="agendado"))
        self.assertFalse(_serialize(self.origem).pode_reabrir)
        self.assertFalse(_serialize(self.origem).pode_reagendar)

    def test_sucessor_pode_ser_reagendado_em_cadeia(self):
        from app.routers.agendamentos import reagendar_agendamento
        from app.schemas import ReagendamentoCreate
        from app.models import Reagendamento
        novo = self.reagendar()
        outro = reagendar_agendamento(novo.id, ReagendamentoCreate(inicio=self.agora + timedelta(days=2), fim=self.agora + timedelta(days=2, minutes=50)), self.db, self.user)
        self.assertEqual(outro.reagendado_de_id, novo.id)
        self.assertEqual(self.db.query(Reagendamento).count(), 2)
        self.assertEqual(self.origem.status, StatusAgendamento.cancelado)

    def test_reagendamento_normaliza_offset_e_grava_data_e_autor(self):
        from app.models import Reagendamento
        novo = self.reagendar(inicio="2026-10-24T19:00:00-03:00", fim="2026-10-24T19:50:00-03:00")
        self.assertEqual(novo.inicio.hour, 22)
        vinculo = self.db.query(Reagendamento).one()
        self.assertEqual(vinculo.criado_em, self.agora)
        self.assertEqual(vinculo.usuario_id, self.user.id)

    def test_horario_que_vence_durante_espera_de_trava_e_recusado(self):
        with patch("app.horarios.agora_utc", side_effect=[self.agora, self.agora + timedelta(days=2)]):
            self.afirmar_recusa(422, self.reagendar)
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_reagendamento_exige_cadastro_ativo(self):
        self.paciente.ativo = False
        self.db.commit()
        self.afirmar_recusa(409, self.reagendar)

    def test_tabela_de_vinculos_pode_ser_adicionada_sem_alterar_original(self):
        from app.models import Reagendamento
        Reagendamento.__table__.drop(self.engine)
        Base.metadata.create_all(self.engine)
        self.db.refresh(self.origem)
        self.assertEqual(self.origem.inicio, datetime(2026, 10, 22, 22))
        self.assertEqual(self.origem.criado_em, datetime(2026, 10, 15, 12))
        self.assertEqual(self.db.query(Reagendamento).count(), 0)

    def test_reabertura_expira_exatamente_no_inicio_da_consulta(self):
        self.origem.inicio = self.agora + timedelta(hours=2)
        self.origem.fim = self.origem.inicio + timedelta(minutes=50)
        self.db.commit()
        self.assertTrue(_serialize(self.origem).pode_reabrir)
        with patch("app.horarios.agora_utc", return_value=self.origem.inicio):
            self.assertFalse(_serialize(self.origem).pode_reabrir)
            self.afirmar_recusa(409, lambda: self.atualizar(status="agendado"))

    def test_status_inicial_nao_permite_contornar_reserva_no_passado(self):
        for status in ["confirmado", "realizado", "cancelado", "falta"]:
            with self.subTest(status=status):
                payload = AgendamentoCreate(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                                            inicio=self.agora - timedelta(hours=1), fim=self.agora,
                                            status=status)
                self.afirmar_recusa(422, lambda: criar_agendamento(payload, self.db, self.user))


if __name__ == "__main__":
    unittest.main()
