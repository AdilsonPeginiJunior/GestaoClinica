"""Rotas AGE-04 via ASGI/JSON com JWT real, banco isolado e sem servidor externo."""
import asyncio
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models import Agendamento, Cargo, Paciente, PerfilUsuario, Permissao, Psicologo, StatusAgendamento, Usuario


class RecorrenciasHTTPTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.agora = datetime(2026, 10, 23, 12)
        clock = patch("app.horarios.agora_utc", return_value=self.agora)
        clock.start()
        self.addCleanup(clock.stop)
        with Session(self.engine) as db:
            permissao = Permissao(chave="agenda:gerenciar", nome="Agenda", descricao="Teste")
            consulta = Permissao(chave="agenda:consultar", nome="Consulta", descricao="Teste")
            cargo = Cargo(nome="Profissional teste", permissoes=[permissao, consulta])
            leitor = Cargo(nome="Leitura teste", permissoes=[consulta])
            pac = Paciente(nome="Paciente fictício")
            psis = [Psicologo(nome=f"Profissional {i}", crp="teste", email=f"p{i}@example.com") for i in range(2)]
            db.add_all([pac, *psis, cargo, leitor])
            db.flush()
            users = [Usuario(nome="Profissional teste", email="p@example.com", senha_hash="teste", perfil=PerfilUsuario.psicologo,
                             psicologo_id=psis[0].id, cargo=cargo),
                     Usuario(nome="Gestão teste", email="g@example.com", senha_hash="teste", perfil=PerfilUsuario.admin, cargo=cargo),
                     Usuario(nome="Leitura teste", email="l@example.com", senha_hash="teste", perfil=PerfilUsuario.recepcionista, cargo=leitor),
                     Usuario(nome="Sem vínculo", email="v@example.com", senha_hash="teste", perfil=PerfilUsuario.psicologo, cargo=cargo)]
            db.add_all(users)
            db.add(Agendamento(paciente_id=pac.id, psicologo_id=psis[0].id,
                               inicio=self.agora - timedelta(days=1), fim=self.agora - timedelta(days=1) + timedelta(minutes=50),
                               status=StatusAgendamento.cancelado))
            db.commit()
            self.pac, self.psis = pac.id, [p.id for p in psis]
        def banco_isolado():
            with Session(self.engine, autoflush=False) as db:
                yield db
        self.overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = banco_isolado
        self.inicio = datetime(2026, 10, 27, 21)

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.overrides)
        self.engine.dispose()

    def request(self, metodo, caminho, dados=None, email="p@example.com"):
        async def executar():
            destino = urlsplit(caminho)
            corpo = json.dumps(dados).encode() if dados is not None else b""
            headers = [(b"content-type", b"application/json")]
            if email is not None:
                token = create_access_token({"sub": email})
                headers.append((b"authorization", f"Bearer {token}".encode()))
            scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": metodo,
                     "scheme": "http", "path": destino.path, "raw_path": destino.path.encode(), "query_string": destino.query.encode(),
                     "root_path": "", "headers": headers, "client": ("127.0.0.1", 1), "server": ("teste", 80)}
            enviados = []
            entregue = False
            async def receber():
                nonlocal entregue
                if not entregue:
                    entregue = True
                    return {"type": "http.request", "body": corpo, "more_body": False}
                await asyncio.Event().wait()
            async def enviar(msg):
                enviados.append(msg)
            await app(scope, receber, enviar)
            status = next(m["status"] for m in enviados if m["type"] == "http.response.start")
            body = b"".join(m.get("body", b"") for m in enviados if m["type"] == "http.response.body")
            return status, json.loads(body)
        return asyncio.run(executar())

    def dados(self, psi=0):
        return dict(paciente_id=self.pac, psicologo_id=self.psis[psi], inicio=self.inicio.isoformat() + "Z",
                    fim=(self.inicio + timedelta(minutes=50)).isoformat() + "Z", intervalo_dias=7)

    def test_criacao_listagem_excecao_e_encerramento_por_jwt(self):
        codigo, r = self.request("POST", "/api/recorrencias", self.dados())
        self.assertEqual(codigo, 201, r)
        self.assertTrue(r["inicio"].endswith("Z"))
        codigo, agenda = self.request("GET", "/api/agendamentos")
        self.assertEqual(codigo, 200)
        agenda = [a for a in agenda if a["recorrencia_id"] == r["id"]]
        self.assertEqual(len(agenda), 13)
        self.assertTrue(all(a["recorrencia_id"] == r["id"] for a in agenda))
        codigo, _ = self.request("PATCH", f"/api/agendamentos/{agenda[0]['id']}", {"status": "cancelado"})
        self.assertEqual(codigo, 200)
        codigo, fim = self.request("POST", f"/api/recorrencias/{r['id']}/encerrar", {"motivo": "Fim da reserva"})
        self.assertEqual(codigo, 200, fim)
        self.assertIsNotNone(fim["encerrada_em"])

    def test_permissoes_nao_autenticado_leitura_e_vinculo(self):
        self.assertEqual(self.request("GET", "/api/recorrencias", email=None)[0], 401)
        self.assertEqual(self.request("POST", "/api/recorrencias", self.dados(), "l@example.com")[0], 403)
        self.assertEqual(self.request("POST", "/api/recorrencias", self.dados(psi=1))[0], 403)
        self.assertEqual(self.request("POST", "/api/recorrencias", self.dados(), "v@example.com")[0], 403)
        self.assertEqual(self.request("GET", "/api/recorrencias", email="v@example.com")[0], 403)
        self.assertEqual(self.request("GET", "/api/agendamentos", email="v@example.com")[0], 403)

    def test_geracao_json_idempotente_e_consulta_nao_grava(self):
        self.assertEqual(self.request("POST", "/api/recorrencias", self.dados())[0], 201)
        codigo, dados = self.request("POST", "/api/recorrencias/gerar")
        self.assertEqual(codigo, 200)
        self.assertEqual(dados["sessoes_criadas"], 0)
        self.assertEqual(self.request("POST", "/api/recorrencias/gerar", email="l@example.com")[0], 403)

    def test_payload_invalido_e_conflito_retornam_mensagem(self):
        dados = self.dados()
        dados["intervalo_dias"] = 15
        self.assertEqual(self.request("POST", "/api/recorrencias", dados)[0], 422)
        self.assertEqual(self.request("POST", "/api/recorrencias", self.dados())[0], 201)
        codigo, resposta = self.request("POST", "/api/recorrencias", self.dados(), "g@example.com")
        self.assertEqual(codigo, 409)
        self.assertIsInstance(resposta["detail"], str)


if __name__ == "__main__":
    unittest.main()
