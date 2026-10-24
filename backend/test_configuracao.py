"""SEG-01: validação de ambiente e inicialização em bancos exclusivamente isolados."""
import asyncio
import os
import secrets
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import BANCO_DEMO, CHAVE_DEMO, Settings
from app.database import Base
from app.models import Agendamento, Cargo, Paciente, PerfilUsuario, Psicologo, Usuario
from app.seed import seed_authorization, seed_database, verificar_banco_producao


class ConfiguracaoTest(unittest.TestCase):
    def setUp(self):
        self.ambiente = patch.dict(os.environ, {}, clear=True)
        self.ambiente.start()
        self.addCleanup(self.ambiente.stop)
        self.chave = secrets.token_urlsafe(48)

    def producao(self, **opcoes):
        dados = dict(app_env="production", secret_key=self.chave, database_url="sqlite:///:memory:", _env_file=None)
        dados.update(opcoes)
        return Settings(**dados)

    def test_demo_padrao_preserva_uso_local(self):
        config = Settings(_env_file=None)
        self.assertEqual(config.app_env, "demo")
        self.assertTrue(config.demo_seed_ativo)
        self.assertEqual(config.database_url, BANCO_DEMO)

    def test_demo_sem_seed_e_producao_sem_seed_por_padrao(self):
        self.assertFalse(Settings(demo_seed=False, _env_file=None).demo_seed_ativo)
        self.assertFalse(self.producao().demo_seed_ativo)

    def test_producao_recusa_chaves_fracas_padrao_e_exemplos(self):
        for chave in ["", "curta", CHAVE_DEMO, "x" * 64, "chave-longa-e-aleatoria-para-producao", " change-me" * 10]:
            with self.subTest(caso=len(chave)), self.assertRaises(ValidationError):
                self.producao(secret_key=chave)

    def test_producao_exige_banco_explicito_e_separado(self):
        for dados in [{}, {"database_url": BANCO_DEMO}, {"database_url": " "},
                      {"database_url": "sqlite:///gestao_clinica.db"},
                      {"database_url": "sqlite:///" + str(Path("gestao_clinica.db").resolve()).replace("\\", "/")},
                      {"database_url": "dsn-invalida"}]:
            with self.subTest(dados=dados), self.assertRaises(ValidationError):
                Settings(app_env="production", secret_key=self.chave, _env_file=None, **dados)

    def test_producao_recusa_seed_e_cors_curinga(self):
        for extra in [dict(demo_seed=True), dict(cors_origins=["*"])]:
            with self.assertRaises(ValidationError):
                self.producao(**extra)

    def test_modo_digitado_errado_e_algoritmo_nao_permitido(self):
        for extra in [dict(app_env="prodution"), dict(algorithm="none"), dict(access_token_expire_minutes=0)]:
            with self.assertRaises(ValidationError):
                Settings(_env_file=None, **extra)

    def test_erros_e_repr_nao_exibem_segredo_ou_url(self):
        config = self.producao(database_url="sqlite:///segredo-de-teste.db")
        self.assertNotIn(self.chave, repr(config))
        self.assertNotIn("segredo-de-teste", repr(config))
        with self.assertRaises(ValidationError) as erro:
            self.producao(demo_seed=True)
        self.assertNotIn(self.chave, str(erro.exception))

    def test_variaveis_de_ambiente_e_dotenv(self):
        with tempfile.TemporaryDirectory(prefix="clinica-config-") as pasta:
            arquivo = Path(pasta) / ".env"
            arquivo.write_text(f"APP_ENV=production\nSECRET_KEY={self.chave}\nDATABASE_URL=sqlite:///:memory:\nDEMO_SEED=false\n", encoding="utf8")
            self.assertEqual(Settings(_env_file=arquivo).app_env, "production")
            with patch.dict(os.environ, {"APP_ENV": "demo", "DEMO_SEED": "true"}):
                self.assertTrue(Settings(_env_file=arquivo).demo_seed_ativo)


class InicializacaoSeguraTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, autoflush=False)
        self.prod = Settings(app_env="production", secret_key=secrets.token_urlsafe(48),
                             database_url="sqlite:///:memory:", _env_file=None)

    def tearDown(self):
        self.engine.dispose()

    def iniciar(self, config):
        from app import main
        async def executar():
            async with main.lifespan(main.app):
                pass
        with patch.object(main, "settings", config), patch.object(main, "engine", self.engine), patch.object(main, "SessionLocal", self.factory):
            asyncio.run(executar())

    def test_startup_producao_cria_catalogo_sem_usuarios_pacientes_ou_agenda(self):
        for _ in range(2):
            self.iniciar(self.prod)
        with self.factory() as db:
            for modelo in [Usuario, Paciente, Psicologo, Agendamento]:
                self.assertEqual(db.query(modelo).count(), 0)
            self.assertGreater(db.query(Cargo).count(), 0)

    def test_seed_direto_nao_consulta_banco_em_producao_ou_demo_desabilitada(self):
        from unittest.mock import Mock
        db = Mock()
        seed_database(db, self.prod)
        seed_database(db, Settings(demo_seed=False, _env_file=None))
        db.query.assert_not_called()
        db.commit.assert_not_called()

    def test_demo_continua_funcionando_e_nao_duplica(self):
        demo = Settings(_env_file=None)
        with patch("app.seed.get_password_hash", return_value="hash-ficticio"):
            self.iniciar(demo)
            self.iniciar(demo)
        with self.factory() as db:
            self.assertEqual(db.query(Usuario).count(), 4)
            self.assertEqual(db.query(Paciente).count(), 6)

    def test_base_demo_nao_e_promovida_nem_apagada(self):
        with self.factory() as db:
            db.add(Usuario(nome="Demo fictício", email="admin@demo.com", perfil=PerfilUsuario.admin, senha_hash="hash-ficticio"))
            db.commit()
        with self.assertRaisesRegex(RuntimeError, "demonstração"):
            self.iniciar(self.prod)
        with self.factory() as db:
            self.assertEqual(db.query(Usuario).count(), 1)

    def test_demo_sem_seed_nao_cria_contas(self):
        self.iniciar(Settings(demo_seed=False, _env_file=None))
        with self.factory() as db:
            self.assertEqual(db.query(Usuario).count(), 0)

    def test_configuracao_publica_nunca_expoe_chave_ou_banco(self):
        from app import main
        with patch.object(main, "settings", self.prod):
            dados = main.configuracao_publica()
        self.assertEqual(dados, {"ambiente": "production", "demo_habilitada": False})

    def test_bootstrap_cria_admin_com_hash_e_nao_redefine(self):
        from app import criar_admin
        from app.auth import verify_password
        self.iniciar(self.prod)
        senha = "Senha-ficticia-teste-42"
        with self.factory() as db, patch.object(criar_admin, "settings", self.prod):
            criar_admin.criar_primeiro_admin(db, "gestao@example.com", "Gestão fictícia", senha)
            user = db.query(Usuario).one()
            self.assertNotEqual(user.senha_hash, senha)
            self.assertTrue(verify_password(senha, user.senha_hash))
            self.assertEqual(user.cargo.nome, "Administrador")
            with self.assertRaisesRegex(ValueError, "Já existe"):
                criar_admin.criar_primeiro_admin(db, "outra@example.com", "Outra", senha)
            self.assertEqual(db.query(Usuario).count(), 1)

    def test_bootstrap_recusa_demo_senha_curta_e_cargo_ausente(self):
        from app import criar_admin
        with self.factory() as db, patch.object(criar_admin, "settings", Settings(_env_file=None)):
            with self.assertRaisesRegex(ValueError, "production"):
                criar_admin.criar_primeiro_admin(db, "g@example.com", "Teste", "Senha-ficticia-teste-42")
        with self.factory() as db, patch.object(criar_admin, "settings", self.prod):
            with self.assertRaises(ValueError):
                criar_admin.criar_primeiro_admin(db, "g@example.com", "Teste", "curta")
            with self.assertRaisesRegex(ValueError, "Inicie a API"):
                criar_admin.criar_primeiro_admin(db, "g@example.com", "Teste", "Senha-ficticia-teste-42")
            self.assertEqual(db.query(Usuario).count(), 0)

    def test_chave_invalida_bloqueia_importacao_em_processo_isolado(self):
        with tempfile.TemporaryDirectory(prefix="clinica-startup-") as pasta:
            env = os.environ.copy()
            env.update(APP_ENV="production", SECRET_KEY="invalida", DEMO_SEED="false",
                       DATABASE_URL="sqlite:///nao-criar.db", PYTHONPATH=str(Path(__file__).parent))
            resultado = subprocess.run([sys.executable, "-c", "import app.main"], env=env, cwd=pasta,
                                       capture_output=True, text=True, timeout=20)
            self.assertNotEqual(resultado.returncode, 0)
            self.assertIn("SECRET_KEY", resultado.stderr)
            self.assertNotIn("input_value", resultado.stderr)
            self.assertFalse((Path(pasta) / "nao-criar.db").exists())

    def test_bootstrap_recusa_endereco_demo_mesmo_com_maiusculas(self):
        from app import criar_admin
        self.iniciar(self.prod)
        with self.factory() as db, patch.object(criar_admin, "settings", self.prod):
            with self.assertRaisesRegex(ValueError, "demonstração"):
                criar_admin.criar_primeiro_admin(db, "ADMIN@demo.com", "Teste", "Senha-ficticia-teste-42")
            self.assertEqual(db.query(Usuario).count(), 0)

    def test_login_e_jwt_demo_bloqueados_em_producao_mesmo_sem_lifespan(self):
        from app import auth, main
        from app.database import get_db
        from test_recorrencias_http import RecorrenciasHTTPTest
        self.iniciar(self.prod)
        with self.factory() as db:
            db.add(Usuario(nome="Demo fictício", email="admin@demo.com", perfil=PerfilUsuario.admin,
                           senha_hash=auth.get_password_hash("demo123")))
            db.commit()
        def banco():
            with self.factory() as db:
                yield db
        anteriores = main.app.dependency_overrides.copy()
        main.app.dependency_overrides[get_db] = banco
        try:
            with patch.object(auth, "settings", self.prod):
                codigo, _ = RecorrenciasHTTPTest.request(self, "POST", "/api/auth/login",
                                                       {"email": "admin@demo.com", "password": "demo123"}, None)
                self.assertEqual(codigo, 401)
                self.assertEqual(RecorrenciasHTTPTest.request(self, "GET", "/api/auth/me", email="admin@demo.com")[0], 401)
        finally:
            main.app.dependency_overrides.clear()
            main.app.dependency_overrides.update(anteriores)

    def test_primeiro_admin_real_faz_login_jwt_e_config_publica_via_asgi(self):
        from app import auth, criar_admin, main
        from app.database import get_db
        from test_recorrencias_http import RecorrenciasHTTPTest
        self.iniciar(self.prod)
        with self.factory() as db, patch.object(criar_admin, "settings", self.prod):
            criar_admin.criar_primeiro_admin(db, "gestao@example.com", "Gestão fictícia", "Senha-ficticia-teste-42")
        def banco():
            with self.factory() as db:
                yield db
        anteriores = main.app.dependency_overrides.copy()
        main.app.dependency_overrides[get_db] = banco
        try:
            with patch.object(auth, "settings", self.prod), patch.object(main, "settings", self.prod):
                codigo, resposta = RecorrenciasHTTPTest.request(self, "POST", "/api/auth/login",
                    {"email": "gestao@example.com", "password": "Senha-ficticia-teste-42"}, None)
                self.assertEqual(codigo, 200)
                self.assertIn("access_token", resposta)
                codigo, me = RecorrenciasHTTPTest.request(self, "GET", "/api/auth/me", email="gestao@example.com")
                self.assertEqual(codigo, 200)
                self.assertIn("agenda:gerenciar", me["permissoes"])
                codigo, publico = RecorrenciasHTTPTest.request(self, "GET", "/api/config/publico", email=None)
                self.assertEqual(codigo, 200)
                self.assertEqual(publico, {"ambiente": "production", "demo_habilitada": False})
        finally:
            main.app.dependency_overrides.clear()
            main.app.dependency_overrides.update(anteriores)


if __name__ == "__main__":
    unittest.main()
