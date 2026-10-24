"""Concorrência AGE-04 com WAL, conexões distintas e processos spawn."""
import multiprocessing
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import recorrencias as regras
from app.database import Base
from app.models import Agendamento, OcorrenciaRecorrencia, Paciente, PerfilUsuario, Psicologo, Recorrencia, StatusAgendamento, Usuario
from app.routers.agendamentos import criar_agendamento
from app.schemas import AgendamentoCreate, RecorrenciaAlterar, RecorrenciaCreate, RecorrenciaEncerrar
from test_concorrencia import engine_temporario


def executar(caminho, usuario_id, dados, operacao, barreira):
    engine = engine_temporario(caminho)
    try:
        with Session(engine, autoflush=False) as db:
            usuario = db.get(Usuario, usuario_id)
            barreira.wait(timeout=20)
            if operacao == "criar":
                regras.criar(db, RecorrenciaCreate(**dados), usuario)
            elif operacao == "avulso":
                criar_agendamento(AgendamentoCreate(**dados), db, usuario)
            elif operacao == "alterar":
                payload = {k: v for k, v in dados.items() if k != "id"}
                regras.alterar(db, dados["id"], RecorrenciaAlterar(**payload), usuario)
            elif operacao == "encerrar":
                regras.encerrar(db, dados["id"], RecorrenciaEncerrar(motivo="Fim"), usuario)
            else:
                if "agora" in dados:
                    with patch("app.horarios.agora_utc", return_value=dados["agora"]):
                        regras.gerar_proximas(db, usuario)
                else:
                    regras.gerar_proximas(db, usuario)
        return "ok"
    except HTTPException as erro:
        return erro.status_code
    finally:
        engine.dispose()


def em_processo(caminho, usuario_id, dados, operacao, barreira, fila):
    try:
        fila.put(executar(caminho, usuario_id, dados, operacao, barreira))
    except Exception as erro:
        fila.put(type(erro).__name__)


class RecorrenciasConcorrenciaTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory(prefix="clinica-recorrencia-")
        self.caminho = str(Path(self.pasta.name) / "teste.db")
        self.engine = engine_temporario(self.caminho)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            pacs = [Paciente(nome=f"Paciente fictício {i}") for i in range(2)]
            psis = [Psicologo(nome=f"Profissional {i}", crp="teste", email=f"p{i}@example.com") for i in range(2)]
            user = Usuario(nome="Gestão", email="g@example.com", senha_hash="teste", perfil=PerfilUsuario.admin)
            db.add_all([*pacs, *psis, user])
            db.commit()
            self.pacs = [p.id for p in pacs]
            self.psis = [p.id for p in psis]
            self.usuario_id = user.id
        self.inicio = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)).replace(second=0, microsecond=0)

    def tearDown(self):
        self.engine.dispose()
        self.pasta.cleanup()

    def dados(self, pac=0, psi=0, semanas=0, serie=True):
        inicio = self.inicio + timedelta(weeks=semanas)
        d = dict(paciente_id=self.pacs[pac], psicologo_id=self.psis[psi], inicio=inicio, fim=inicio + timedelta(minutes=50))
        if serie:
            d["intervalo_dias"] = 7
        return d

    def competir(self, operacoes):
        barreira = threading.Barrier(len(operacoes))
        with ThreadPoolExecutor(max_workers=len(operacoes)) as pool:
            futuros = [pool.submit(executar, self.caminho, self.usuario_id, dados, op, barreira) for dados, op in operacoes]
            return [f.result(timeout=30) for f in futuros]

    def criar(self):
        with Session(self.engine, autoflush=False) as db:
            regras.criar(db, RecorrenciaCreate(**self.dados()), db.get(Usuario, self.usuario_id))

    def test_duas_regras_mesmo_profissional(self):
        self.assertCountEqual(self.competir([(self.dados(), "criar"), (self.dados(pac=1), "criar")]), ["ok", 409])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Recorrencia).count(), 1)

    def test_duas_regras_mesmo_paciente_profissionais_diferentes(self):
        self.assertCountEqual(self.competir([(self.dados(), "criar"), (self.dados(psi=1), "criar")]), ["ok", 409])

    def test_regra_e_avulso_fora_do_horizonte(self):
        self.assertCountEqual(self.competir([(self.dados(), "criar"), (self.dados(pac=1, semanas=100, serie=False), "avulso")]), ["ok", 409])

    def test_geracao_paralela_nao_duplica(self):
        self.criar()
        with Session(self.engine) as db:
            antes = db.query(Agendamento).count()
        with patch("app.horarios.agora_utc", return_value=self.inicio + timedelta(days=60)):
            self.assertEqual(self.competir([({}, "gerar")] * 4), ["ok"] * 4)
        with Session(self.engine) as db:
            self.assertGreater(db.query(Agendamento).count(), antes)
            self.assertEqual(db.query(OcorrenciaRecorrencia).count(), db.query(Agendamento).count())

    def test_geracao_em_processos_independentes(self):
        self.criar()
        contexto = multiprocessing.get_context("spawn")
        barreira, fila = contexto.Barrier(2), contexto.Queue()
        dados = {"agora": self.inicio + timedelta(days=60)}
        processos = [contexto.Process(target=em_processo, args=(self.caminho, self.usuario_id, dados, "gerar", barreira, fila)) for _ in range(2)]
        try:
            for p in processos:
                p.start()
            resultados = [fila.get(timeout=30) for _ in processos]
            for p in processos:
                p.join(timeout=10)
                self.assertEqual(p.exitcode, 0)
            self.assertEqual(resultados, ["ok", "ok"])
            with Session(self.engine) as db:
                self.assertEqual(db.query(Agendamento).count(), db.query(OcorrenciaRecorrencia).count())
        finally:
            for p in processos:
                if p.is_alive():
                    p.terminate()
                    p.join()
            fila.close()

    def mudanca(self):
        with Session(self.engine) as db:
            ident = db.query(Recorrencia.id).scalar()
        inicio = self.inicio + timedelta(days=1)
        return dict(id=ident, inicio=inicio, fim=inicio + timedelta(minutes=50),
                    a_partir_de=self.inicio, intervalo_dias=7, motivo="Mudança")

    def test_duas_alteracoes_da_mesma_regra(self):
        self.criar()
        dados = self.mudanca()
        self.assertCountEqual(self.competir([(dados, "alterar"), (dados, "alterar")]), ["ok", 409])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Recorrencia).count(), 2)

    def test_alteracao_disputa_horario_futuro_com_avulso(self):
        self.criar()
        dados = self.mudanca()
        reserva = self.dados(pac=1, semanas=100, serie=False)
        reserva["inicio"] += timedelta(days=1)
        reserva["fim"] += timedelta(days=1)
        self.assertCountEqual(self.competir([(dados, "alterar"), (reserva, "avulso")]), ["ok", 409])

    def test_encerramento_disputa_com_geracao(self):
        self.criar()
        with Session(self.engine) as db:
            ident = db.query(Recorrencia.id).scalar()
        resultados = self.competir([({"id": ident}, "encerrar"), ({}, "gerar")])
        self.assertEqual(resultados, ["ok", "ok"])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Agendamento).filter(Agendamento.status.in_([
                StatusAgendamento.agendado, StatusAgendamento.confirmado])).count(), 0)


if __name__ == "__main__":
    unittest.main()
