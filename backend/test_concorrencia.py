"""Concorrência real em SQLite temporário, com sessões e processos independentes."""

import multiprocessing
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    Agendamento, Cargo, EstornoFinanceiro, LancamentoFinanceiro, Paciente,
    PerfilUsuario, Permissao, Prontuario, Psicologo, StatusAgendamento as Status, Usuario,
)
from app.routers.agendamentos import atualizar_agendamento
from app.routers.prontuario import criar_evolucao
from app.schemas import AgendamentoUpdate, ProntuarioCreate
from app.services import aplicar_status_agendamento
from app.transacoes import bloquear_agendamento


def engine_temporario(caminho):
    engine = create_engine("sqlite:///" + Path(caminho).as_posix(),
                           connect_args={"check_same_thread": False, "timeout": 5})

    @event.listens_for(engine, "connect")
    def configurar(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")

    return engine


def realizar_em_processo(caminho, agendamento_id, usuario_id, barreira, fila):
    """Worker de teste; conecta somente no arquivo temporário informado."""
    engine = engine_temporario(caminho)
    try:
        with Session(engine, autoflush=False) as db:
            user = db.get(Usuario, usuario_id)
            ag = db.get(Agendamento, agendamento_id)
            barreira.wait(timeout=15)
            aplicar_status_agendamento(db, ag, Status.realizado, usuario=user)
            fila.put("ok")
    except Exception as exc:
        fila.put(type(exc).__name__)
    finally:
        engine.dispose()


class ConcorrenciaTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory(prefix="gestao-clinica-teste-")
        self.caminho = str(Path(self.pasta.name) / "concorrencia.db")
        self.engine = engine_temporario(self.caminho)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            paciente = Paciente(nome="Paciente fictício")
            psi = Psicologo(nome="Profissional fictício", crp="teste", email="psi@example.com")
            outro = Psicologo(nome="Outro fictício", crp="outro", email="outro@example.com")
            cargo = Cargo(nome="Gestão", permissoes=[
                Permissao(chave="financeiro:gerenciar", nome="Gerenciar", descricao="Teste"),
            ])
            gestor = Usuario(nome="Gestão fictícia", email="gestao@example.com", senha_hash="nao-utilizado",
                             perfil=PerfilUsuario.admin, cargo=cargo)
            db.add_all([paciente, psi, outro, gestor])
            db.flush()
            profissional = Usuario(nome="Profissional", email="profissional@example.com", senha_hash="nao-utilizado",
                                   perfil=PerfilUsuario.psicologo, psicologo_id=psi.id)
            ag = Agendamento(paciente_id=paciente.id, psicologo_id=psi.id,
                             inicio=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2),
                             fim=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2, minutes=50))
            db.add_all([profissional, ag])
            db.commit()
            self.ag_id, self.gestor_id = ag.id, gestor.id
            self.profissional_id, self.outro_id = profissional.id, outro.id

    def tearDown(self):
        self.engine.dispose()
        self.pasta.cleanup()

    def realizar(self):
        with Session(self.engine, autoflush=False) as db:
            aplicar_status_agendamento(db, self.ag_id, Status.realizado)

    def executar(self, operacao, barreira):
        with Session(self.engine, autoflush=False) as db:
            usuario_id = self.profissional_id if operacao == "evoluir" else self.gestor_id
            user = db.get(Usuario, usuario_id)
            # Ambos os concorrentes começam com uma cópia potencialmente antiga.
            ag = db.get(Agendamento, self.ag_id)
            barreira.wait(timeout=10)
            try:
                if operacao == "evoluir":
                    criar_evolucao(ProntuarioCreate(agendamento_id=self.ag_id, evolucao="Evolução fictícia"), db, user)
                elif operacao == "trocar":
                    atualizar_agendamento(self.ag_id, AgendamentoUpdate(psicologo_id=self.outro_id), db, user)
                elif operacao == "anotar":
                    atualizar_agendamento(self.ag_id, AgendamentoUpdate(observacoes="Observação fictícia"), db, user)
                else:
                    status = Status.realizado if operacao == "realizar" else Status.cancelado
                    aplicar_status_agendamento(db, ag, status, usuario=user, motivo="Correção operacional")
                return "ok"
            except HTTPException as exc:
                return exc.status_code

    def competir(self, *operacoes):
        barreira = threading.Barrier(len(operacoes))
        with ThreadPoolExecutor(max_workers=len(operacoes)) as pool:
            tarefas = [pool.submit(self.executar, op, barreira) for op in operacoes]
            return [t.result(timeout=20) for t in tarefas]

    def test_seis_realizacoes_simultaneas_faturam_uma_vez(self):
        self.assertEqual(self.competir(*(["realizar"] * 6)), ["ok"] * 6)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Agendamento, self.ag_id).status, Status.realizado)
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 2)
            self.assertEqual({l.chave_automatica for l in db.query(LancamentoFinanceiro)}, {"receita", "repasse"})

    def test_dois_cancelamentos_simultaneos_estornam_uma_vez(self):
        self.realizar()
        self.assertEqual(self.competir("cancelar", "cancelar"), ["ok", "ok"])
        with Session(self.engine) as db:
            self.assertEqual(db.get(Agendamento, self.ag_id).status, Status.cancelado)
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 4)
            self.assertEqual(db.query(EstornoFinanceiro).count(), 2)

    def test_cancelamento_e_evolucao_nao_criam_prontuario_cancelado(self):
        self.realizar()
        self.assertCountEqual(self.competir("cancelar", "evoluir"), ["ok", 409])
        with Session(self.engine) as db:
            ag = db.get(Agendamento, self.ag_id)
            if db.query(Prontuario).count():
                self.assertEqual(ag.status, Status.realizado)
                self.assertEqual(db.query(LancamentoFinanceiro).count(), 2)
                self.assertEqual(db.query(EstornoFinanceiro).count(), 0)
            else:
                self.assertEqual(ag.status, Status.cancelado)
                self.assertEqual(db.query(LancamentoFinanceiro).count(), 4)

    def test_duas_evolucoes_simultaneas_criam_um_registro(self):
        self.realizar()
        self.assertCountEqual(self.competir("evoluir", "evoluir"), ["ok", 409])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Prontuario).count(), 1)

    def disputar_com_ordem_definida(self, primeiro, segundo):
        self.realizar()
        barreira = threading.Barrier(2)
        with Session(self.engine, autoflush=False) as db:
            bloquear_agendamento(db, self.ag_id)
            usuario_id = self.profissional_id if primeiro == "evoluir" else self.gestor_id
            user = db.get(Usuario, usuario_id)
            with ThreadPoolExecutor(max_workers=1) as pool:
                tarefa = pool.submit(self.executar, segundo, barreira)
                # O segundo já leu o atendimento antigo antes de liberar o primeiro.
                barreira.wait(timeout=10)
                if primeiro == "evoluir":
                    criar_evolucao(ProntuarioCreate(agendamento_id=self.ag_id, evolucao="Evolução fictícia"), db, user)
                else:
                    aplicar_status_agendamento(db, self.ag_id, Status.cancelado, usuario=user, motivo="Correção operacional")
                self.assertEqual(tarefa.result(timeout=10), 409)

    def test_evolucao_primeiro_bloqueia_cancelamento_que_leu_estado_antigo(self):
        self.disputar_com_ordem_definida("evoluir", "cancelar")
        with Session(self.engine) as db:
            self.assertEqual(db.get(Agendamento, self.ag_id).status, Status.realizado)
            self.assertEqual(db.query(Prontuario).count(), 1)
            self.assertEqual(db.query(EstornoFinanceiro).count(), 0)

    def test_cancelamento_primeiro_bloqueia_evolucao_que_leu_estado_antigo(self):
        self.disputar_com_ordem_definida("cancelar", "evoluir")
        with Session(self.engine) as db:
            self.assertEqual(db.get(Agendamento, self.ag_id).status, Status.cancelado)
            self.assertEqual(db.query(Prontuario).count(), 0)
            self.assertEqual(db.query(EstornoFinanceiro).count(), 2)

    def test_troca_de_profissional_e_realizacao_preservam_vinculos(self):
        resultados = self.competir("trocar", "realizar")
        self.assertEqual(resultados[1], "ok")
        self.assertIn(resultados[0], ["ok", 409])
        with Session(self.engine) as db:
            ag = db.get(Agendamento, self.ag_id)
            lancamentos = db.query(LancamentoFinanceiro).all()
            self.assertEqual(len(lancamentos), 2)
            self.assertTrue(all(l.psicologo_id == ag.psicologo_id for l in lancamentos))

    def test_realizar_e_cancelar_preservam_consistencia(self):
        resultados = self.competir("realizar", "cancelar")
        self.assertEqual(resultados[1], "ok")
        self.assertIn(resultados[0], ["ok", 409])
        with Session(self.engine) as db:
            self.assertEqual(db.get(Agendamento, self.ag_id).status, Status.cancelado)
            lancamentos = db.query(LancamentoFinanceiro).all()
            self.assertIn(len(lancamentos), [0, 4])
            self.assertEqual(sum(l.valor for l in lancamentos), 0)

    def test_patch_sem_status_nao_desfaz_realizacao_concorrente(self):
        self.assertEqual(self.competir("anotar", "realizar"), ["ok", "ok"])
        with Session(self.engine) as db:
            ag = db.get(Agendamento, self.ag_id)
            self.assertEqual(ag.status, Status.realizado)
            self.assertEqual(ag.observacoes, "Observação fictícia")
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 2)

    def test_autorizacao_considera_vinculo_atual_mesmo_com_cache_antigo(self):
        with Session(self.engine, autoflush=False) as antigo:
            ag_cache = antigo.get(Agendamento, self.ag_id)
            profissional = antigo.get(Usuario, self.profissional_id)
            with Session(self.engine, autoflush=False) as atual:
                gestor = atual.get(Usuario, self.gestor_id)
                atualizar_agendamento(self.ag_id, AgendamentoUpdate(psicologo_id=self.outro_id), atual, gestor)
            with self.assertRaises(HTTPException) as erro:
                aplicar_status_agendamento(antigo, ag_cache, Status.realizado, usuario=profissional)
            self.assertEqual(erro.exception.status_code, 403)
        with Session(self.engine) as db:
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 0)

    def test_timeout_da_trava_retorna_409_e_permite_nova_tentativa(self):
        with Session(self.engine, autoflush=False) as primeiro, Session(self.engine, autoflush=False) as segundo:
            bloquear_agendamento(primeiro, self.ag_id)
            segundo.connection().exec_driver_sql("PRAGMA busy_timeout=0")
            with self.assertRaises(HTTPException) as erro:
                aplicar_status_agendamento(segundo, self.ag_id, Status.realizado)
            self.assertEqual(erro.exception.status_code, 409)
            self.assertFalse(segundo.in_transaction())
            primeiro.rollback()
            aplicar_status_agendamento(segundo, self.ag_id, Status.realizado)
            self.assertEqual(segundo.query(LancamentoFinanceiro).count(), 2)

    def test_dois_processos_independentes_nao_duplicam_faturamento(self):
        ctx = multiprocessing.get_context("spawn")
        barreira, fila = ctx.Barrier(2), ctx.Queue()
        processos = [ctx.Process(target=realizar_em_processo,
                                args=(self.caminho, self.ag_id, self.gestor_id, barreira, fila)) for _ in range(2)]
        try:
            for processo in processos:
                processo.start()
            for processo in processos:
                processo.join(timeout=20)
                self.assertFalse(processo.is_alive(), "Worker excedeu o tempo do teste")
                self.assertEqual(processo.exitcode, 0)
            self.assertEqual([fila.get(timeout=2) for _ in processos], ["ok", "ok"])
        finally:
            for processo in processos:
                if processo.is_alive():
                    processo.terminate()
                    processo.join(timeout=5)
            fila.close()
            fila.join_thread()
        with Session(self.engine) as db:
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 2)


if __name__ == "__main__":
    unittest.main()
