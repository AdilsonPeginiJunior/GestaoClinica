"""SEG-02: matriz real de permissões por JSON/ASGI/JWT, somente dados fictícios."""
import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (Agendamento, Cargo, EstornoFinanceiro, LancamentoFinanceiro, Paciente,
                        PerfilUsuario, Permissao, Prontuario, Psicologo, Recorrencia, StatusAgendamento, TipoLancamento, Usuario)
from app.seed import seed_authorization


class IsolamentoTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, autoflush=False)
        with self.factory() as db:
            seed_authorization(db)
            cargos = {c.nome: c for c in db.query(Cargo)}
            permissoes = {p.chave: p for p in db.query(Permissao)}
            keys = ["dashboard:acessar", "pacientes:consultar", "pacientes:gerenciar", "psicologos:consultar",
                    "psicologos:gerenciar", "agenda:consultar", "agenda:gerenciar", "financeiro:consultar",
                    "financeiro:gerenciar", "prontuario:ler_proprio", "prontuario:criar", "relatorios:consultar_proprio"]
            custom = Cargo(nome="Cargo personalizado", permissoes=[permissoes[k] for k in keys])
            amplo = Cargo(nome="Leitura ampla explícita", permissoes=list(permissoes.values()))
            vazio = Cargo(nome="Sem permissões")
            pacs = [Paciente(nome=f"Paciente fictício {i}", cpf=f"ficticio-{i}", ativo=True) for i in range(4)]
            psis = [Psicologo(nome=f"Profissional fictício {i}", crp="teste", email=f"psi{i}@example.com") for i in range(2)]
            db.add_all([custom, amplo, vazio, *pacs, *psis])
            db.flush()
            contas = [
                ("psi", PerfilUsuario.psicologo, psis[0].id, cargos["Psicólogo"]),
                ("custom", PerfilUsuario.psicologo, psis[0].id, custom),
                ("amplo", PerfilUsuario.psicologo, psis[0].id, amplo),
                ("sem", PerfilUsuario.psicologo, None, amplo),
                ("inexistente", PerfilUsuario.psicologo, 99999, amplo),
                ("recepcao", PerfilUsuario.recepcionista, None, cargos["Recepção"]),
                ("gestao", PerfilUsuario.admin, None, cargos["Administrador"]),
                ("socia", PerfilUsuario.socia, None, cargos["Sócia"]),
                ("vazio", PerfilUsuario.recepcionista, None, vazio),
            ]
            users = {}
            for nome, perfil, pid, cargo in contas:
                user = Usuario(nome=f"Usuário fictício {nome}", email=f"{nome}@example.com", senha_hash="nao-utilizado",
                               perfil=perfil, psicologo_id=pid, cargo=cargo, ativo=True)
                db.add(user)
                users[nome] = user
            db.flush()
            self.futuro = datetime.now().replace(microsecond=0) + timedelta(days=8)
            passado = self.futuro - timedelta(days=10)
            ags = []
            for pac, psi, inicio, status in [(0, 0, passado, "realizado"), (1, 1, passado, "realizado"),
                                            (2, 0, self.futuro, "agendado"), (2, 1, self.futuro + timedelta(hours=2), "agendado"),
                                            (0, 0, passado - timedelta(days=1), "realizado")]:
                ag = Agendamento(paciente_id=pacs[pac].id, psicologo_id=psis[psi].id,
                                 inicio=inicio, fim=inicio + timedelta(minutes=50), status=StatusAgendamento(status))
                db.add(ag)
                ags.append(ag)
            db.flush()
            for i in range(2):
                db.add(Prontuario(paciente_id=pacs[i].id, psicologo_id=psis[i].id,
                                 agendamento_id=ags[i].id, evolucao=f"Evolução fictícia profissional {i}"))
                original = LancamentoFinanceiro(psicologo_id=psis[i].id, agendamento_id=ags[i].id,
                    descricao=f"Original fictício {i}", tipo=TipoLancamento.receita, valor=220, automatico=True)
                estorno = LancamentoFinanceiro(psicologo_id=psis[i].id, agendamento_id=ags[i].id,
                    descricao=f"Estorno fictício {i}", tipo=TipoLancamento.receita, valor=-220, automatico=True)
                db.add_all([original, estorno])
                db.flush()
                db.add(EstornoFinanceiro(lancamento_original_id=original.id, lancamento_estorno_id=estorno.id,
                                        usuario_id=users["gestao"].id, motivo=f"Motivo fictício {i}"))
            db.add(LancamentoFinanceiro(descricao="Lançamento geral fictício", tipo=TipoLancamento.receita, valor=50, automatico=False))
            db.commit()
            self.pacs, self.psis, self.ags = [p.id for p in pacs], [p.id for p in psis], [a.id for a in ags]
        def banco():
            with self.factory() as db:
                yield db
        self.overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = banco

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.overrides)
        self.engine.dispose()

    def request(self, metodo, caminho, dados=None, user="psi"):
        from test_recorrencias_http import RecorrenciasHTTPTest
        return RecorrenciasHTTPTest.request(self, metodo, caminho, dados, f"{user}@example.com" if user else None)

    def reserva(self, paciente=0, psi=0, dias=0):
        inicio = self.futuro + timedelta(days=dias)
        return dict(paciente_id=self.pacs[paciente], psicologo_id=self.psis[psi], inicio=inicio.isoformat() + "Z",
                    fim=(inicio + timedelta(minutes=50)).isoformat() + "Z")

    def test_sem_vinculo_ou_vinculo_inexistente_falha_fechado_em_todas_as_listas(self):
        caminhos = ["/api/dashboard", "/api/pacientes", "/api/psicologos", "/api/agendamentos", "/api/recorrencias",
                    "/api/prontuario", "/api/prontuario/atendimentos-disponiveis", "/api/financeiro/lancamentos",
                    "/api/financeiro/estornos", f"/api/relatorios/psicologo/{self.psis[1]}"]
        for user in ["sem", "inexistente"]:
            for caminho in caminhos:
                with self.subTest(user=user, caminho=caminho):
                    self.assertEqual(self.request("GET", caminho, user=user)[0], 403)

    def test_sem_vinculo_nao_escreve_por_ids_adivinhados(self):
        operacoes = [("POST", "/api/agendamentos", self.reserva()),
                     ("PATCH", f"/api/agendamentos/{self.ags[0]}", {"status": "cancelado"}),
                     ("POST", "/api/recorrencias", dict(**self.reserva(), intervalo_dias=7)),
                     ("POST", "/api/recorrencias/gerar", None),
                     ("PATCH", f"/api/pacientes/{self.pacs[0]}", {"nome": "Alterado"}),
                     ("POST", "/api/financeiro/lancamentos", {"descricao": "Teste", "valor": 1}),
                     ("POST", "/api/prontuario", {"agendamento_id": self.ags[1], "evolucao": "Teste"})]
        for metodo, caminho, dados in operacoes:
            with self.subTest(caminho=caminho):
                self.assertEqual(self.request(metodo, caminho, dados, "sem")[0], 403)

    def test_dashboard_e_pacientes_usam_o_mesmo_escopo(self):
        for user in ["psi", "custom"]:
            codigo, dados = self.request("GET", "/api/dashboard", user=user)
            self.assertEqual(codigo, 200)
            self.assertEqual(dados["total_pacientes"], 2)
            self.assertEqual(dados["total_agendamentos"], 3)
            codigo, lista = self.request("GET", "/api/pacientes", user=user)
            self.assertEqual(codigo, 200)
            self.assertCountEqual([p["id"] for p in lista], [self.pacs[0], self.pacs[2]])

    def test_busca_de_paciente_nao_vaza_por_nome(self):
        self.assertEqual(self.request("GET", "/api/pacientes?q=fict%C3%ADcio%201")[1], [])

    def test_get_e_patch_de_outro_paciente_retornam_mesmo_404_de_inexistente(self):
        for ident in [self.pacs[1], self.pacs[3], 99999]:
            with self.subTest(ident=ident):
                self.assertEqual(self.request("GET", f"/api/pacientes/{ident}")[0], 404)
                self.assertEqual(self.request("PATCH", f"/api/pacientes/{ident}", {"nome": "Teste"}, "custom")[0], 404)

    def test_custom_pode_editar_paciente_proprio_sem_ganhar_acesso_global(self):
        codigo, dados = self.request("PATCH", f"/api/pacientes/{self.pacs[0]}", {"telefone": "ficticio"}, "custom")
        self.assertEqual(codigo, 200)
        self.assertEqual(dados["telefone"], "ficticio")

    def test_profissional_nao_cria_cadastro_global_nem_altera_repasse(self):
        self.assertEqual(self.request("POST", "/api/pacientes", {"nome": "Novo"}, "custom")[0], 403)
        self.assertEqual(self.request("PATCH", f"/api/psicologos/{self.psis[0]}", {"percentual_repasse": 100}, "custom")[0], 403)

    def test_recepcao_e_gestao_veem_cadastro_administrativo_sem_prontuario(self):
        for user in ["recepcao", "gestao", "socia"]:
            codigo, dados = self.request("GET", "/api/pacientes", user=user)
            self.assertEqual(codigo, 200)
            self.assertEqual(len(dados), 4)
            self.assertFalse(any("evolucao" in p for p in dados))
            self.assertEqual(self.request("GET", "/api/prontuario", user=user)[0], 403)

    def test_recepcao_faz_primeiro_agendamento_e_vincula_visibilidade(self):
        self.assertEqual(self.request("POST", "/api/agendamentos", self.reserva(paciente=3, dias=2), "recepcao")[0], 201)
        self.assertEqual(self.request("GET", f"/api/pacientes/{self.pacs[3]}")[0], 200)

    def test_profissional_nao_inicia_agendamento_ou_serie_com_paciente_de_outro(self):
        for paciente in [1, 3]:
            dados = self.reserva(paciente=paciente, dias=2)
            self.assertEqual(self.request("POST", "/api/agendamentos", dados)[0], 404)
            self.assertEqual(self.request("POST", "/api/recorrencias", dict(**dados, intervalo_dias=7))[0], 404)

    def test_profissional_cria_agendamento_e_serie_para_paciente_proprio(self):
        self.assertEqual(self.request("POST", "/api/agendamentos", self.reserva(dias=2))[0], 201)
        self.assertEqual(self.request("POST", "/api/recorrencias", dict(**self.reserva(dias=3), intervalo_dias=14))[0], 201)

    def test_agenda_e_filtro_nao_mostram_atendimento_de_outro(self):
        for user in ["psi", "custom"]:
            codigo, dados = self.request("GET", f"/api/agendamentos?psicologo_id={self.psis[1]}", user=user)
            self.assertEqual(codigo, 200)
            self.assertTrue(all(a["psicologo_id"] == self.psis[0] for a in dados))

    def test_nao_muda_status_ou_reagenda_atendimento_de_outro(self):
        ag = self.ags[3]
        self.assertEqual(self.request("PATCH", f"/api/agendamentos/{ag}", {"status": "cancelado"})[0], 403)
        dados = self.reserva(dias=2)
        self.assertEqual(self.request("POST", f"/api/agendamentos/{ag}/reagendar", {k: dados[k] for k in ["inicio", "fim"]})[0], 403)

    def test_catalogo_profissional_restrito_ao_proprio(self):
        codigo, dados = self.request("GET", "/api/psicologos")
        self.assertEqual(codigo, 200)
        self.assertEqual([p["id"] for p in dados], [self.psis[0]])
        self.assertEqual(self.request("GET", f"/api/psicologos/{self.psis[1]}")[0], 404)

    def test_relatorio_proprio_e_permissao_ampla_explicita(self):
        self.assertEqual(self.request("GET", f"/api/relatorios/psicologo/{self.psis[0]}")[0], 200)
        self.assertEqual(self.request("GET", f"/api/relatorios/psicologo/{self.psis[1]}", user="custom")[0], 403)
        self.assertEqual(self.request("GET", f"/api/relatorios/psicologo/{self.psis[1]}", user="amplo")[0], 200)

    def test_prontuario_proprio_mesmo_quando_paciente_compartilhado(self):
        codigo, dados = self.request("GET", "/api/prontuario")
        self.assertEqual(codigo, 200)
        self.assertEqual([r["psicologo_id"] for r in dados], [self.psis[0]])
        codigo, dados = self.request("GET", "/api/prontuario", user="amplo")
        self.assertEqual(codigo, 200)
        self.assertEqual(len(dados), 2)

    def test_evolucao_so_em_atendimento_proprio(self):
        self.assertEqual(self.request("POST", "/api/prontuario", {"agendamento_id": self.ags[1], "evolucao": "Teste"})[0], 403)
        self.assertEqual(self.request("POST", "/api/prontuario", {"agendamento_id": self.ags[4], "evolucao": "Teste fictício"})[0], 201)

    def test_financeiro_e_estornos_de_cargo_customizado_so_proprios(self):
        codigo, dados = self.request("GET", "/api/financeiro/lancamentos", user="custom")
        self.assertEqual(codigo, 200)
        self.assertEqual(len(dados), 2)
        self.assertTrue(all(l["psicologo_id"] == self.psis[0] for l in dados))
        self.assertEqual(self.request("GET", f"/api/financeiro/lancamentos?psicologo_id={self.psis[1]}", user="custom")[1], [])
        codigo, dados = self.request("GET", "/api/financeiro/estornos", user="custom")
        self.assertEqual(codigo, 200)
        self.assertEqual(len(dados), 1)
        self.assertEqual(self.request("GET", f"/api/financeiro/estornos?agendamento_id={self.ags[1]}", user="custom")[1], [])

    def test_lancamento_manual_nao_pode_apontar_para_outro_profissional(self):
        dados = {"descricao": "Teste fictício", "valor": 10, "psicologo_id": self.psis[1]}
        self.assertEqual(self.request("POST", "/api/financeiro/lancamentos", dados, "custom")[0], 403)

    def test_lancamento_manual_nao_pode_apontar_atendimento_alheio(self):
        dados = {"descricao": "Teste fictício", "valor": 10, "psicologo_id": self.psis[0], "agendamento_id": self.ags[1]}
        self.assertEqual(self.request("POST", "/api/financeiro/lancamentos", dados, "custom")[0], 403)

    def test_lancamento_manual_proprio_sem_profissional_e_atribuido_ao_usuario(self):
        codigo, dados = self.request("POST", "/api/financeiro/lancamentos", {"descricao": "Teste fictício", "valor": 10}, "custom")
        self.assertEqual(codigo, 201)
        self.assertEqual(dados["psicologo_id"], self.psis[0])

    def test_financeiro_default_negado_e_gestao_ampla_permitida(self):
        self.assertEqual(self.request("GET", "/api/financeiro/lancamentos")[0], 403)
        self.assertEqual(self.request("GET", "/api/financeiro/lancamentos", user="gestao")[0], 200)
        self.assertEqual(len(self.request("GET", "/api/financeiro/lancamentos", user="gestao")[1]), 5)

    def test_cargo_vazio_ou_sessao_ausente_nao_concede_permissoes(self):
        for caminho in ["/api/pacientes", "/api/agendamentos", "/api/dashboard", "/api/prontuario", "/api/financeiro/lancamentos"]:
            self.assertEqual(self.request("GET", caminho, user="vazio")[0], 403)
            self.assertEqual(self.request("GET", caminho, user=None)[0], 401)

    def test_socios_e_profissionais_nao_administram_cargos(self):
        for user in ["socia", "custom", "amplo", "recepcao"]:
            self.assertEqual(self.request("GET", "/api/admin/usuarios", user=user)[0], 403)

    def test_permissao_revogada_e_cargo_removido_valem_no_proximo_jwt(self):
        self.assertEqual(self.request("GET", "/api/pacientes", user="custom")[0], 200)
        with self.factory() as db:
            user = db.query(Usuario).filter_by(email="custom@example.com").one()
            user.cargo.permissoes = []
            db.commit()
        self.assertEqual(self.request("GET", "/api/pacientes", user="custom")[0], 403)
        with self.factory() as db:
            user = db.query(Usuario).filter_by(email="psi@example.com").one()
            user.cargo_id = None
            db.commit()
        self.assertEqual(self.request("GET", "/api/pacientes")[0], 403)

    def test_usuario_inativo_nao_acessa_dados(self):
        with self.factory() as db:
            db.query(Usuario).filter_by(email="custom@example.com").update({"ativo": False})
            db.commit()
        self.assertEqual(self.request("GET", "/api/pacientes", user="custom")[0], 401)

    def test_leitura_ampla_de_relatorios_disponibiliza_catalogo_sem_liberar_agenda_alheia(self):
        codigo, catalogo = self.request("GET", "/api/psicologos", user="amplo")
        self.assertEqual(codigo, 200)
        self.assertEqual(len(catalogo), 2)
        self.assertEqual(self.request("GET", f"/api/psicologos/{self.psis[1]}", user="amplo")[0], 200)
        dados = self.request("GET", "/api/agendamentos", user="amplo")[1]
        self.assertTrue(all(a["psicologo_id"] == self.psis[0] for a in dados))

    def test_serie_alheia_nao_e_listada_alterada_encerrada_ou_expandida(self):
        dados = dict(**self.reserva(paciente=1, psi=1, dias=4), intervalo_dias=7)
        codigo, regra = self.request("POST", "/api/recorrencias", dados, "gestao")
        self.assertEqual(codigo, 201)
        self.assertEqual(self.request("GET", "/api/recorrencias", user="custom")[1], [])
        self.assertEqual(self.request("POST", f"/api/recorrencias/{regra['id']}/encerrar", {"motivo": "Teste"}, "custom")[0], 403)
        mudanca = {"a_partir_de": dados["inicio"], "inicio": dados["inicio"], "fim": dados["fim"],
                   "intervalo_dias": 7, "motivo": "Teste"}
        self.assertEqual(self.request("POST", f"/api/recorrencias/{regra['id']}/alterar", mudanca, "custom")[0], 403)
        self.assertEqual(self.request("POST", "/api/recorrencias/gerar", user="custom")[1]["sessoes_criadas"], 0)
        self.assertIsNone(self.request("GET", "/api/recorrencias", user="gestao")[1][0]["encerrada_em"])

    def test_vinculo_historico_por_regra_sem_sessoes_geradas_conta_para_visibilidade(self):
        with self.factory() as db:
            user = db.query(Usuario).filter_by(email="gestao@example.com").one()
            db.add(Recorrencia(paciente_id=self.pacs[3], psicologo_id=self.psis[0], inicio=self.futuro,
                              intervalo_dias=7, duracao_minutos=50, usuario_id=user.id,
                              encerrada_em=self.futuro - timedelta(days=1)))
            db.commit()
        self.assertEqual(self.request("GET", f"/api/pacientes/{self.pacs[3]}")[0], 200)
        self.assertEqual(self.request("GET", "/api/dashboard")[1]["total_pacientes"], 3)

    def test_gestao_nao_grava_vinculos_financeiros_inexistentes_ou_incoerentes(self):
        for dados in [dict(psicologo_id=99999), dict(agendamento_id=99999),
                      dict(psicologo_id=self.psis[0], agendamento_id=self.ags[1])]:
            with self.subTest(dados=dados):
                codigo, _ = self.request("POST", "/api/financeiro/lancamentos", dict(descricao="Teste", valor=10, **dados), "gestao")
                self.assertIn(codigo, [404, 422])
        with self.factory() as db:
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 5)

    def test_escritas_negadas_nao_deixam_registros_parciais(self):
        self.request("POST", "/api/financeiro/lancamentos", {"descricao": "Teste", "valor": 10, "psicologo_id": self.psis[1]}, "custom")
        self.request("POST", "/api/recorrencias", dict(**self.reserva(paciente=3, dias=4), intervalo_dias=7))
        self.request("POST", "/api/agendamentos", self.reserva(paciente=3, dias=4))
        with self.factory() as db:
            self.assertEqual(db.query(LancamentoFinanceiro).count(), 5)
            self.assertEqual(db.query(Agendamento).count(), 5)
            self.assertEqual(db.query(Recorrencia).count(), 0)


if __name__ == "__main__":
    unittest.main()
