"""Compatibilidade e unicidade do schema financeiro, somente em memória."""

import asyncio
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.schema_financeiro import atualizar_schema_financeiro
from app.models import LancamentoFinanceiro, Usuario


class SchemaFinanceiroTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

    def tearDown(self):
        self.engine.dispose()

    def schema_antigo(self):
        with self.engine.begin() as conn:
            conn.exec_driver_sql("""CREATE TABLE lancamentos_financeiros (
                id INTEGER PRIMARY KEY, agendamento_id INTEGER, psicologo_id INTEGER,
                descricao VARCHAR(255) NOT NULL, tipo VARCHAR(7) NOT NULL,
                valor FLOAT NOT NULL, data_lancamento DATETIME, automatico BOOLEAN
            )""")
            conn.exec_driver_sql("""CREATE TABLE estornos_financeiros (
                id INTEGER PRIMARY KEY, lancamento_original_id INTEGER UNIQUE NOT NULL,
                lancamento_estorno_id INTEGER UNIQUE NOT NULL,
                usuario_id INTEGER NOT NULL, motivo VARCHAR(500), criado_em DATETIME
            )""")

    def inserir(self, registros):
        with self.engine.begin() as conn:
            conn.execute(text("""INSERT INTO lancamentos_financeiros
                (id, agendamento_id, psicologo_id, descricao, tipo, valor, automatico)
                VALUES (:id, :ag, :psi, :descricao, :tipo, :valor, :automatico)"""), registros)

    def test_schema_novo_e_idempotencia(self):
        Base.metadata.create_all(self.engine)
        atualizar_schema_financeiro(self.engine)
        atualizar_schema_financeiro(self.engine)
        indices = inspect(self.engine).get_indexes("lancamentos_financeiros")
        self.assertTrue(any(i["name"] == "uq_lancamento_chave_automatica" and i["unique"] for i in indices))

    def test_schema_antigo_preserva_valores_e_classifica_apenas_reconhecidos(self):
        self.schema_antigo()
        self.inserir([
            dict(id=1, ag=10, psi=1, descricao="Receita sessao #10 - Paciente fictício", tipo="receita", valor=220, automatico=True),
            dict(id=2, ag=10, psi=1, descricao="Repasse psicologo #10 - Profissional fictício", tipo="repasse", valor=132, automatico=True),
            dict(id=3, ag=10, psi=None, descricao="Receita clinica sessao #10", tipo="receita", valor=88, automatico=True),
            dict(id=4, ag=10, psi=1, descricao="Receita sessao #10 - Manual fictício", tipo="receita", valor=10, automatico=False),
            dict(id=5, ag=10, psi=1, descricao="Estorno do lançamento #1", tipo="receita", valor=-220, automatico=True),
            dict(id=6, ag=10, psi=1, descricao="Estorno do lançamento #2", tipo="repasse", valor=-132, automatico=True),
            dict(id=7, ag=20, psi=1, descricao="Automático de origem desconhecida", tipo="receita", valor=50, automatico=True),
        ])
        with self.engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO estornos_financeiros VALUES (1,1,5,1,'Correção',NULL),(2,2,6,1,'Correção',NULL)")
            antes = conn.exec_driver_sql("SELECT id,agendamento_id,psicologo_id,descricao,tipo,valor,automatico FROM lancamentos_financeiros ORDER BY id").all()
        atualizar_schema_financeiro(self.engine)
        atualizar_schema_financeiro(self.engine)
        with self.engine.connect() as conn:
            depois = conn.exec_driver_sql("SELECT id,agendamento_id,psicologo_id,descricao,tipo,valor,automatico FROM lancamentos_financeiros ORDER BY id").all()
            chaves = conn.exec_driver_sql("SELECT chave_automatica FROM lancamentos_financeiros ORDER BY id").scalars().all()
        self.assertEqual(antes, depois)
        self.assertEqual(chaves, ["receita", "repasse", None, None, "estorno:1", "estorno:2", None])

    def test_duplicacao_legada_bloqueia_atualizacao_sem_apagar_dados(self):
        self.schema_antigo()
        self.inserir([
            dict(id=i, ag=10, psi=1, descricao="Receita sessao #10 - Paciente fictício", tipo="receita", valor=220, automatico=True)
            for i in [1, 2]
        ])
        with self.assertRaisesRegex(RuntimeError, "duplicado.*10"):
            atualizar_schema_financeiro(self.engine)
        with self.engine.connect() as conn:
            self.assertEqual(conn.exec_driver_sql("SELECT COUNT(*) FROM lancamentos_financeiros").scalar(), 2)
        self.assertNotIn("chave_automatica", {c["name"] for c in inspect(self.engine).get_columns("lancamentos_financeiros")})

    def test_indice_rejeita_chave_repetida_mesmo_fora_dos_servicos(self):
        self.schema_antigo()
        atualizar_schema_financeiro(self.engine)
        with self.engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO lancamentos_financeiros (id,agendamento_id,descricao,tipo,valor,automatico,chave_automatica) VALUES (1,10,'Original','receita',220,1,'receita')")
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as conn:
                conn.exec_driver_sql("INSERT INTO lancamentos_financeiros (id,agendamento_id,descricao,tipo,valor,automatico,chave_automatica) VALUES (2,10,'Duplicado','receita',220,1,'receita')")

    def test_receitas_manuais_repetidas_nao_sao_restringidas(self):
        self.schema_antigo()
        atualizar_schema_financeiro(self.engine)
        with self.engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO lancamentos_financeiros (id,agendamento_id,descricao,tipo,valor,automatico) VALUES (1,10,'Manual','receita',10,0),(2,10,'Manual','receita',20,0)")
            self.assertEqual(conn.exec_driver_sql("SELECT COUNT(*) FROM lancamentos_financeiros").scalar(), 2)

    def test_lifespan_atualiza_schema_antigo_e_seed_sem_duplicar_ao_reiniciar(self):
        from app import main
        self.schema_antigo()

        async def iniciar_duas_vezes():
            for _ in range(2):
                async with main.lifespan(main.app):
                    with Session(self.engine) as db:
                        self.assertEqual(db.query(Usuario).count(), 4)
                        lancamentos = db.query(LancamentoFinanceiro).all()
                        self.assertEqual(len(lancamentos), 4)
                        self.assertTrue(all(l.chave_automatica in {"receita", "repasse"} for l in lancamentos))

        with patch.object(main, "engine", self.engine), patch.object(main, "SessionLocal", sessionmaker(bind=self.engine)), patch("app.seed.get_password_hash", return_value="hash-ficticio-sem-login"):
            asyncio.run(iniciar_duas_vezes())

    def test_lifespan_interrompe_antes_do_seed_quando_ha_duplicacao_legada(self):
        from app import main
        self.schema_antigo()
        self.inserir([
            dict(id=i, ag=10, psi=1, descricao="Receita sessao #10 - Paciente fictício", tipo="receita", valor=220, automatico=True)
            for i in [1, 2]
        ])

        async def iniciar():
            async with main.lifespan(main.app):
                self.fail("Não deveria liberar a aplicação com duplicação legada")

        with patch.object(main, "engine", self.engine), patch.object(main, "SessionLocal", sessionmaker(bind=self.engine)), patch.object(main, "seed_database") as seed:
            with self.assertRaisesRegex(RuntimeError, "duplicado"):
                asyncio.run(iniciar())
            seed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
