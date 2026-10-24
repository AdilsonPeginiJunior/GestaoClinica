"""Transições e cancelamentos com banco isolado, sem dados da clínica."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    Agendamento, Cargo, LancamentoFinanceiro, Paciente, PerfilUsuario,
    Permissao, Prontuario, Psicologo, StatusAgendamento as Status, TipoLancamento, Usuario,
)
from app.routers.agendamentos import atualizar_agendamento
from app.routers.dashboard import dashboard, relatorio_psicologo
from app.routers.financeiro import listar_estornos
from app.schemas import AgendamentoUpdate, EstornoRead
from app.services import aplicar_status_agendamento


class StatusAgendamentoTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.agora = datetime.utcnow()
        self.relogio = patch("app.horarios.agora_utc", return_value=self.agora - timedelta(days=1))
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.contador_horarios = 0
        self.paciente = Paciente(nome="Paciente fictício")
        self.psi = Psicologo(nome="Profissional fictício", crp="teste", email="psi@example.com",
                            percentual_repasse=60)
        cargo = Cargo(nome="Gestão", permissoes=[
            Permissao(chave="financeiro:gerenciar", nome="Gerenciar", descricao="Teste"),
            Permissao(chave="financeiro:consultar", nome="Consultar", descricao="Teste"),
            Permissao(chave="relatorios:consultar_todos", nome="Relatórios", descricao="Teste"),
        ])
        self.user = Usuario(nome="Gestão fictícia", email="gestao@example.com",
                            senha_hash="nao-utilizado", perfil=PerfilUsuario.admin, cargo=cargo)
        self.db.add_all([self.paciente, self.psi, self.user])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def agendamento(self, status=Status.agendado):
        inicio = self.agora + timedelta(hours=self.contador_horarios)
        self.contador_horarios += 1
        ag = Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                         inicio=inicio, fim=inicio + timedelta(minutes=50))
        self.db.add(ag)
        self.db.commit()
        if status == Status.realizado:
            aplicar_status_agendamento(self.db, ag, status)
        else:
            ag.status = status
            self.db.commit()
        return ag

    def atualizar(self, ag, **payload):
        return atualizar_agendamento(ag.id, AgendamentoUpdate(**payload), self.db, self.user)

    def test_matriz_completa_de_transicoes(self):
        permitidas = {
            Status.agendado: set(Status),
            Status.confirmado: set(Status),
            Status.realizado: {Status.realizado, Status.cancelado},
            Status.cancelado: {Status.cancelado, Status.agendado},
            Status.falta: {Status.falta, Status.agendado},
        }
        for origem in Status:
            for destino in Status:
                with self.subTest(origem=origem.value, destino=destino.value):
                    ag = self.agendamento(origem)
                    if destino in permitidas[origem]:
                        self.atualizar(ag, status=destino, motivo_cancelamento="Correção operacional")
                        self.assertEqual(ag.status, destino)
                    else:
                        with self.assertRaises(HTTPException) as erro:
                            self.atualizar(ag, status=destino)
                        self.assertEqual(erro.exception.status_code, 409)
                        self.db.refresh(ag)
                        self.assertEqual(ag.status, origem)

    def test_estorno_preserva_originais_e_zera_totais(self):
        ag = self.agendamento(Status.realizado)
        originais = [(l.id, l.valor, l.tipo) for l in ag.lancamentos]
        self.psi.percentual_repasse = 90
        self.db.commit()
        self.atualizar(ag, status="cancelado", motivo_cancelamento="  Lançado por engano  ")
        from app.models import EstornoFinanceiro
        registros = self.db.query(EstornoFinanceiro).all()
        self.assertEqual(len(registros), 2)
        for original_id, valor, tipo in originais:
            original = self.db.get(LancamentoFinanceiro, original_id)
            self.assertEqual((original.valor, original.tipo), (valor, tipo))
            registro = next(r for r in registros if r.lancamento_original_id == original_id)
            compensacao = self.db.get(LancamentoFinanceiro, registro.lancamento_estorno_id)
            self.assertEqual((compensacao.valor, compensacao.tipo), (-valor, tipo))
            self.assertEqual(compensacao.psicologo_id, self.psi.id)
            self.assertEqual(registro.usuario_id, self.user.id)
            self.assertEqual(registro.motivo, "Lançado por engano")
        painel = dashboard(db=self.db, current_user=self.user)
        self.assertEqual((painel.receita_periodo, painel.repasse_periodo), (0, 0))
        relatorio = relatorio_psicologo(
            self.psi.id, db=self.db, current_user=self.user,
            data_inicio=self.agora - timedelta(seconds=1), data_fim=self.agora + timedelta(minutes=1),
        )
        self.assertEqual((relatorio.receita_bruta, relatorio.repasse_total), (0, 0))
        self.assertEqual(relatorio.sessoes_realizadas, 0)

    def test_repetir_cancelamento_nao_duplica_estorno(self):
        ag = self.agendamento(Status.realizado)
        self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.atualizar(ag, status="cancelado", motivo_cancelamento="Repetição")
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 4)

    def test_cancelamento_realizado_exige_permissao_financeira(self):
        ag = self.agendamento(Status.realizado)
        self.user.cargo = None
        self.db.commit()
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.assertEqual(erro.exception.status_code, 403)
        self.assertEqual(ag.status, Status.realizado)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)

    def test_cancelamento_realizado_exige_motivo(self):
        for motivo in [None, "", "   "]:
            with self.subTest(motivo=motivo):
                ag = self.agendamento(Status.realizado)
                with self.assertRaises(HTTPException) as erro:
                    self.atualizar(ag, status="cancelado", motivo_cancelamento=motivo)
                self.assertEqual(erro.exception.status_code, 422)
                self.assertEqual(ag.status, Status.realizado)

    def test_prontuario_impede_cancelamento_e_troca_de_vinculos(self):
        ag = self.agendamento(Status.realizado)
        self.db.add(Prontuario(paciente_id=self.paciente.id, psicologo_id=self.psi.id,
                              agendamento_id=ag.id, evolucao="Evolução fictícia"))
        self.db.commit()
        for payload in [dict(status="cancelado", motivo_cancelamento="Erro"),
                        dict(paciente_id=999), dict(psicologo_id=999),
                        dict(inicio=self.agora + timedelta(days=1)), dict(fim=self.agora)]:
            with self.subTest(payload=payload):
                with self.assertRaises(HTTPException) as erro:
                    self.atualizar(ag, **payload)
                self.assertEqual(erro.exception.status_code, 409)
        self.assertEqual(self.db.query(Prontuario).one().agendamento_id, ag.id)
        self.assertEqual(ag.status, Status.realizado)

    def test_patch_misto_invalido_nao_persiste_campos(self):
        ag = self.agendamento(Status.realizado)
        with self.assertRaises(HTTPException):
            self.atualizar(ag, status="agendado", observacoes="Não deve persistir")
        self.db.refresh(ag)
        self.assertIsNone(ag.observacoes)
        self.assertEqual(ag.status, Status.realizado)

    def test_nao_reabre_cancelamento_com_financeiro(self):
        ag = self.agendamento(Status.realizado)
        resposta = self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.assertTrue(resposta.possui_historico_financeiro)
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, status="agendado")
        self.assertEqual(erro.exception.status_code, 409)
        self.assertEqual(ag.status, Status.cancelado)

    def test_estorno_ignora_parcela_legada_e_lancamento_manual(self):
        ag = self.agendamento(Status.realizado)
        self.db.add_all([
            LancamentoFinanceiro(agendamento_id=ag.id, descricao=f"Receita clinica sessao #{ag.id}",
                                 tipo=TipoLancamento.receita, valor=88, automatico=True),
            LancamentoFinanceiro(agendamento_id=ag.id, descricao="Receita manual",
                                 tipo=TipoLancamento.receita, valor=10, automatico=False),
        ])
        self.db.commit()
        self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 6)
        self.assertEqual(dashboard(db=self.db, current_user=self.user).receita_periodo, 10)

    def test_falha_ao_gravar_estorno_reverte_status_e_compensacoes(self):
        ag = self.agendamento(Status.realizado)
        def falhar_apos_flush():
            self.db.flush()
            raise RuntimeError("Falha simulada após escrita na transação")
        with patch.object(self.db, "commit", side_effect=falhar_apos_flush):
            with self.assertRaises(RuntimeError):
                self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.db.refresh(ag)
        self.assertEqual(ag.status, Status.realizado)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)

    def test_nao_altera_vinculos_de_realizado_sem_prontuario(self):
        ag = self.agendamento(Status.realizado)
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, psicologo_id=999)
        self.assertEqual(erro.exception.status_code, 409)
        self.db.refresh(ag)
        self.assertEqual(ag.psicologo_id, self.psi.id)

    def test_status_nulo_e_rejeitado(self):
        ag = self.agendamento()
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, status=None)
        self.assertEqual(erro.exception.status_code, 422)

    def test_historico_incompleto_nao_pode_ser_cancelado(self):
        ag = self.agendamento(Status.realizado)
        self.db.query(LancamentoFinanceiro).filter(
            LancamentoFinanceiro.tipo == TipoLancamento.repasse).delete()
        self.db.commit()
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.assertEqual(erro.exception.status_code, 409)
        self.assertEqual(ag.status, Status.realizado)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 1)

    def test_realizado_sem_financeiro_nao_e_cancelado_silenciosamente(self):
        ag = self.agendamento()
        ag.status = Status.realizado
        self.db.commit()
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        self.assertEqual(erro.exception.status_code, 409)
        self.assertEqual(ag.status, Status.realizado)

    def test_vinculos_de_cancelado_com_financeiro_tambem_sao_protegidos(self):
        ag = self.agendamento(Status.realizado)
        self.atualizar(ag, status="cancelado", motivo_cancelamento="Erro operacional")
        with self.assertRaises(HTTPException) as erro:
            self.atualizar(ag, inicio=self.agora + timedelta(days=1))
        self.assertEqual(erro.exception.status_code, 409)
        self.assertEqual(ag.inicio, self.agora)

    def test_consulta_de_estornos_filtra_por_atendimento(self):
        ag = self.agendamento(Status.realizado)
        outro = self.agendamento(Status.realizado)
        self.atualizar(ag, status="cancelado", motivo_cancelamento="Primeiro cancelamento")
        self.atualizar(outro, status="cancelado", motivo_cancelamento="Segundo cancelamento")
        registros = listar_estornos(db=self.db, _=self.user, agendamento_id=ag.id)
        self.assertEqual(len(registros), 2)
        for registro in registros:
            self.assertEqual(EstornoRead.model_validate(registro).motivo, "Primeiro cancelamento")
        self.assertEqual(len(listar_estornos(db=self.db, _=self.user, agendamento_id=None)), 4)

    def test_estorno_em_outro_mes_preserva_periodo_original(self):
        ag = self.agendamento(Status.realizado)
        mes_anterior = self.agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        originais = self.db.query(LancamentoFinanceiro).all()
        for lancamento in originais:
            lancamento.data_lancamento = mes_anterior
        self.db.commit()
        self.atualizar(ag, status="cancelado", motivo_cancelamento="Correção posterior")
        painel = dashboard(db=self.db, current_user=self.user)
        self.assertEqual((painel.receita_periodo, painel.repasse_periodo), (-220, -132))
        for original in originais:
            self.assertEqual(original.data_lancamento, mes_anterior)

    def test_reabertura_sem_financeiro_pode_ser_realizada_depois(self):
        ag = self.agendamento(Status.cancelado)
        self.atualizar(ag, status="agendado")
        self.atualizar(ag, status="realizado")
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)
        self.assertEqual(ag.status, Status.realizado)

    def test_tabela_nova_pode_ser_adicionada_sem_recriar_tabelas_existentes(self):
        # Simula o create_all do protótipo sobre um schema anterior à tabela de estornos.
        from app.models import EstornoFinanceiro
        engine_legado = create_engine("sqlite:///:memory:")
        try:
            tabelas_antigas = [t for t in Base.metadata.sorted_tables if t is not EstornoFinanceiro.__table__]
            Base.metadata.create_all(engine_legado, tables=tabelas_antigas)
            with engine_legado.begin() as conn:
                conn.execute(Paciente.__table__.insert().values(nome="Sentinela fictícia"))
            self.assertNotIn("estornos_financeiros", inspect(engine_legado).get_table_names())
            Base.metadata.create_all(engine_legado)
            with Session(engine_legado) as db:
                self.assertEqual(db.query(Paciente).one().nome, "Sentinela fictícia")
            self.assertIn("estornos_financeiros", inspect(engine_legado).get_table_names())
        finally:
            engine_legado.dispose()


if __name__ == "__main__":
    unittest.main()
