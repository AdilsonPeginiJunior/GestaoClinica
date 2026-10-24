"""Reservas concorrentes por profissional/paciente em SQLite temporário com WAL."""

import multiprocessing
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Agendamento, Paciente, PerfilUsuario, Psicologo, StatusAgendamento, Usuario
from app.routers.agendamentos import criar_agendamento, atualizar_agendamento, reagendar_agendamento
from app.schemas import AgendamentoCreate, AgendamentoUpdate, ReagendamentoCreate
from test_concorrencia import engine_temporario


def reservar_em_processo(caminho, dados, usuario_id, barreira, fila):
    engine = engine_temporario(caminho)
    try:
        with Session(engine, autoflush=False) as db:
            user = db.get(Usuario, usuario_id)
            barreira.wait(timeout=15)
            criar_agendamento(AgendamentoCreate(**dados), db, user)
            fila.put("ok")
    except HTTPException as exc:
        fila.put(exc.status_code)
    except Exception as exc:
        fila.put(type(exc).__name__)
    finally:
        engine.dispose()


def reagendar_em_processo(caminho, agendamento_id, dados, usuario_id, barreira, fila):
    engine = engine_temporario(caminho)
    try:
        with Session(engine, autoflush=False) as db:
            user = db.get(Usuario, usuario_id)
            db.get(Agendamento, agendamento_id)
            barreira.wait(timeout=15)
            reagendar_agendamento(agendamento_id, ReagendamentoCreate(**dados), db, user)
            fila.put("ok")
    except HTTPException as exc:
        fila.put(exc.status_code)
    except Exception as exc:
        fila.put(type(exc).__name__)
    finally:
        engine.dispose()


class AgendaConcorrenciaTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory(prefix="gestao-clinica-reservas-")
        self.caminho = str(Path(self.pasta.name) / "reservas.db")
        self.engine = engine_temporario(self.caminho)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            pacientes = [Paciente(nome=f"Paciente fictício {i}") for i in range(2)]
            psis = [Psicologo(nome=f"Profissional fictício {i}", crp=f"teste-{i}", email=f"psi{i}@example.com") for i in range(2)]
            user = Usuario(nome="Gestão fictícia", email="gestao@example.com", senha_hash="nao-utilizado", perfil=PerfilUsuario.admin)
            db.add_all([*pacientes, *psis, user])
            db.commit()
            self.pac_ids, self.psi_ids, self.user_id = [p.id for p in pacientes], [p.id for p in psis], user.id
        self.inicio = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)

    def tearDown(self):
        self.engine.dispose()
        self.pasta.cleanup()

    def dados(self, paciente=0, psi=0, deslocamento=0):
        inicio = self.inicio + timedelta(minutes=deslocamento)
        return dict(paciente_id=self.pac_ids[paciente], psicologo_id=self.psi_ids[psi], inicio=inicio, fim=inicio + timedelta(minutes=50))

    def operacao(self, dados, barreira, agendamento_id=None, status=None):
        with Session(self.engine, autoflush=False) as db:
            user = db.get(Usuario, self.user_id)
            db.get(Psicologo, self.psi_ids[0])
            if agendamento_id:
                db.get(Agendamento, agendamento_id)
            barreira.wait(timeout=10)
            try:
                if agendamento_id and status == "reagendar":
                    reagendar_agendamento(agendamento_id, ReagendamentoCreate(**dados), db, user)
                elif agendamento_id:
                    atualizar_agendamento(agendamento_id, AgendamentoUpdate(**dados, **({"status": status} if status else {})), db, user)
                else:
                    criar_agendamento(AgendamentoCreate(**dados), db, user)
                return "ok"
            except HTTPException as exc:
                return exc.status_code

    def competir(self, operacoes):
        barreira = threading.Barrier(len(operacoes))
        with ThreadPoolExecutor(max_workers=len(operacoes)) as pool:
            tarefas = [pool.submit(self.operacao, dados, barreira, ag_id, status) for dados, ag_id, status in operacoes]
            return [t.result(timeout=15) for t in tarefas]

    def contar_ocupados(self):
        with Session(self.engine) as db:
            return db.query(Agendamento).filter(Agendamento.status.in_([
                StatusAgendamento.agendado, StatusAgendamento.confirmado, StatusAgendamento.realizado,
            ]), Agendamento.inicio == self.inicio).count()

    def test_dois_post_mesmo_profissional_reservam_uma_vez(self):
        self.assertCountEqual(self.competir([(self.dados(), None, None), (self.dados(paciente=1), None, None)]), ["ok", 409])
        self.assertEqual(self.contar_ocupados(), 1)

    def test_dois_post_mesmo_paciente_reservam_uma_vez(self):
        self.assertCountEqual(self.competir([(self.dados(), None, None), (self.dados(psi=1), None, None)]), ["ok", 409])
        self.assertEqual(self.contar_ocupados(), 1)

    def test_post_adjacentes_sao_permitidos_mesmo_profissional(self):
        self.assertEqual(self.competir([(self.dados(), None, None), (self.dados(paciente=1, deslocamento=50), None, None)]), ["ok", "ok"])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Agendamento).count(), 2)

    def test_post_de_recursos_independentes_podem_coexistir(self):
        self.assertEqual(self.competir([(self.dados(), None, None), (self.dados(paciente=1, psi=1), None, None)]), ["ok", "ok"])
        self.assertEqual(self.contar_ocupados(), 2)

    def preparar_agendamento(self, dados, status="agendado"):
        with Session(self.engine, autoflush=False) as db:
            return criar_agendamento(AgendamentoCreate(**dados, status=status), db, db.get(Usuario, self.user_id)).id

    def test_dois_reagendamentos_disputam_o_mesmo_horario(self):
        ag1 = self.preparar_agendamento(self.dados(deslocamento=-180))
        ag2 = self.preparar_agendamento(self.dados(paciente=1, deslocamento=-120))
        alvo = dict(inicio=self.inicio, fim=self.inicio + timedelta(minutes=50))
        self.assertCountEqual(self.competir([(alvo, ag1, None), (alvo, ag2, None)]), ["ok", 409])
        self.assertEqual(self.contar_ocupados(), 1)

    def test_criacao_e_reagendamento_disputam_o_mesmo_horario(self):
        ag = self.preparar_agendamento(self.dados(deslocamento=-120))
        alvo = dict(inicio=self.inicio, fim=self.inicio + timedelta(minutes=50))
        self.assertCountEqual(self.competir([(alvo, ag, None), (self.dados(paciente=1), None, None)]), ["ok", 409])
        self.assertEqual(self.contar_ocupados(), 1)

    def test_criacao_e_reabertura_disputam_o_mesmo_horario(self):
        ag = self.preparar_agendamento(self.dados(), status="cancelado")
        self.assertCountEqual(self.competir([({}, ag, "agendado"), (self.dados(paciente=1), None, None)]), ["ok", 409])
        self.assertEqual(self.contar_ocupados(), 1)

    def test_inativacao_primeiro_impede_reserva_com_cache_antigo(self):
        barreira = threading.Barrier(2)
        with Session(self.engine, autoflush=False) as db:
            db.execute(update(Psicologo).where(Psicologo.id == self.psi_ids[0]).values(ativo=False))
            with ThreadPoolExecutor(max_workers=1) as pool:
                tarefa = pool.submit(self.operacao, self.dados(), barreira)
                barreira.wait(timeout=10)
                db.commit()
                self.assertEqual(tarefa.result(timeout=10), 409)
        self.assertEqual(self.contar_ocupados(), 0)

    def test_dois_processos_nao_reservam_o_mesmo_profissional(self):
        ctx = multiprocessing.get_context("spawn")
        barreira, fila = ctx.Barrier(2), ctx.Queue()
        processos = [ctx.Process(target=reservar_em_processo,
                                args=(self.caminho, self.dados(paciente=i), self.user_id, barreira, fila)) for i in range(2)]
        try:
            for processo in processos:
                processo.start()
            for processo in processos:
                processo.join(timeout=20)
                self.assertFalse(processo.is_alive(), "Worker excedeu o tempo do teste")
                self.assertEqual(processo.exitcode, 0)
            self.assertCountEqual([fila.get(timeout=2) for _ in processos], ["ok", 409])
        finally:
            for processo in processos:
                if processo.is_alive():
                    processo.terminate()
                    processo.join(timeout=5)
            fila.close()
            fila.join_thread()
        self.assertEqual(self.contar_ocupados(), 1)

    def test_reagendamentos_concorrentes_criam_um_unico_sucessor(self):
        from app.models import Reagendamento
        ag = self.preparar_agendamento(self.dados(deslocamento=-120), status="cancelado")
        alvo1 = dict(inicio=self.inicio, fim=self.inicio + timedelta(minutes=50))
        alvo2 = dict(inicio=self.inicio + timedelta(days=1), fim=self.inicio + timedelta(days=1, minutes=50))
        self.assertCountEqual(self.competir([(alvo1, ag, "reagendar"), (alvo2, ag, "reagendar")]), ["ok", 409])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Reagendamento).count(), 1)
            self.assertEqual(db.query(Agendamento).count(), 2)

    def test_reagendamento_e_nova_reserva_disputam_o_mesmo_horario(self):
        ag = self.preparar_agendamento(self.dados(deslocamento=-120), status="cancelado")
        alvo = dict(inicio=self.inicio, fim=self.inicio + timedelta(minutes=50))
        self.assertCountEqual(self.competir([(alvo, ag, "reagendar"), (self.dados(paciente=1), None, None)]), ["ok", 409])
        self.assertEqual(self.contar_ocupados(), 1)

    def test_dois_processos_reagendam_original_uma_unica_vez(self):
        from app.models import Reagendamento
        ag = self.preparar_agendamento(self.dados(deslocamento=-120), status="cancelado")
        ctx = multiprocessing.get_context("spawn")
        barreira, fila = ctx.Barrier(2), ctx.Queue()
        processos = [ctx.Process(target=reagendar_em_processo,
                                args=(self.caminho, ag, self.dados(deslocamento=i * 120), self.user_id, barreira, fila)) for i in range(2)]
        try:
            for processo in processos:
                processo.start()
            for processo in processos:
                processo.join(timeout=20)
                self.assertFalse(processo.is_alive(), "Worker excedeu o tempo do teste")
                self.assertEqual(processo.exitcode, 0)
            self.assertCountEqual([fila.get(timeout=2) for _ in processos], ["ok", 409])
        finally:
            for processo in processos:
                if processo.is_alive():
                    processo.terminate()
                    processo.join(timeout=5)
            fila.close()
            fila.join_thread()
        with Session(self.engine) as db:
            self.assertEqual(db.query(Reagendamento).count(), 1)
            self.assertEqual(db.query(Agendamento).count(), 2)


if __name__ == "__main__":
    unittest.main()
