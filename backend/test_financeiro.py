r"""Regressões financeiras em SQLite em memória, sem seed ou banco da clínica.

Na pasta backend: ..\.venv\Scripts\python.exe -m unittest -v test_financeiro
"""

import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    Agendamento, Cargo, LancamentoFinanceiro, Paciente, PerfilUsuario,
    Permissao, Psicologo, StatusAgendamento, TipoAtendimento, TipoLancamento, Usuario,
)
from app.routers.dashboard import dashboard, relatorio_psicologo
from app.services import aplicar_status_agendamento


class FinanceiroTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.agora = datetime.utcnow()
        cargo = Cargo(nome="Gestão teste", permissoes=[
            Permissao(chave="financeiro:consultar", nome="Financeiro", descricao="Teste"),
            Permissao(chave="relatorios:consultar_todos", nome="Relatórios", descricao="Teste"),
        ])
        self.user = Usuario(nome="Teste", email="gestao@example.com", senha_hash="nao-utilizado",
                            perfil=PerfilUsuario.admin, cargo=cargo)
        self.paciente = Paciente(nome="Paciente fictício", tipo_atendimento=TipoAtendimento.particular)
        self.psicologo = Psicologo(nome="Profissional fictício", crp="teste", email="psi@example.com",
                                  percentual_repasse=60)
        self.db.add_all([self.user, self.paciente, self.psicologo])
        self.db.commit()
        self.ag = Agendamento(paciente_id=self.paciente.id, psicologo_id=self.psicologo.id,
                              inicio=self.agora, fim=self.agora + timedelta(minutes=50))
        self.db.add(self.ag)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def realizar(self):
        aplicar_status_agendamento(self.db, self.ag, StatusAgendamento.realizado)

    def painel(self):
        return dashboard(db=self.db, current_user=self.user)

    def adicionar_receita(self, descricao, valor, automatico=False, agendamento_id=None,
                          psicologo_id=None, data=None):
        self.db.add(LancamentoFinanceiro(
            descricao=descricao, tipo=TipoLancamento.receita, valor=valor,
            automatico=automatico, agendamento_id=agendamento_id,
            psicologo_id=psicologo_id, data_lancamento=data or self.agora,
        ))
        self.db.commit()

    def test_sessao_particular_gera_apenas_receita_e_repasse(self):
        self.realizar()
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)
        receita = self.db.query(func.sum(LancamentoFinanceiro.valor)).filter(
            LancamentoFinanceiro.tipo == TipoLancamento.receita).scalar()
        self.assertEqual(receita, 220)
        painel = self.painel()
        self.assertEqual(painel.receita_periodo, 220)
        self.assertEqual(painel.repasse_periodo, 132)
        self.assertEqual(painel.receita_periodo - painel.repasse_periodo, 88)

    def test_repetir_realizado_nao_duplica(self):
        self.realizar()
        self.realizar()
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)
        self.assertEqual(self.painel().receita_periodo, 220)

    def test_convenio(self):
        self.paciente.tipo_atendimento = TipoAtendimento.convenio
        self.realizar()
        painel = self.painel()
        self.assertEqual(painel.receita_periodo, 160)
        self.assertEqual(painel.repasse_periodo, 96)
        self.assertEqual(painel.receita_periodo - painel.repasse_periodo, 64)

    def test_repasse_zero(self):
        self.psicologo.percentual_repasse = 0
        self.realizar()
        self.assertEqual(self.painel().receita_periodo, 220)
        self.assertEqual(self.painel().repasse_periodo, 0)

    def test_repasse_integral(self):
        self.psicologo.percentual_repasse = 100
        self.realizar()
        self.assertEqual(self.painel().receita_periodo, 220)
        self.assertEqual(self.painel().repasse_periodo, 220)

    def test_legado_nao_infla_painel_e_registro_e_preservado(self):
        self.realizar()
        # Reproduz o terceiro lançamento gerado pela versão antiga.
        self.adicionar_receita(f"Receita clinica sessao #{self.ag.id}", 88,
                               automatico=True, agendamento_id=self.ag.id)
        quantidade = self.db.query(LancamentoFinanceiro).count()
        self.assertEqual(self.painel().receita_periodo, 220)
        self.assertEqual(self.painel().repasse_periodo, 132)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), quantidade)

    def test_receitas_legitimas_sem_profissional_continuam_na_soma(self):
        # Cada lançamento difere do legado em um critério: não basta filtrar nulos/prefixo.
        descricao = f"Receita clinica sessao #{self.ag.id}"
        self.adicionar_receita(descricao, 10, agendamento_id=self.ag.id)
        self.adicionar_receita(descricao, 20, automatico=True)
        self.adicionar_receita("Outra receita automática", 30,
                               automatico=True, agendamento_id=self.ag.id)
        self.adicionar_receita(f"Receita clinica sessao #{self.ag.id + 1}", 40,
                               automatico=True, agendamento_id=self.ag.id)
        self.adicionar_receita(descricao, 50, automatico=True,
                               agendamento_id=self.ag.id, psicologo_id=self.psicologo.id)
        self.assertEqual(self.painel().receita_periodo, 150)

    def test_relatorio_por_profissional_confere_com_painel(self):
        self.realizar()
        relatorio = relatorio_psicologo(
            self.psicologo.id, db=self.db, current_user=self.user,
            data_inicio=self.agora - timedelta(seconds=1),
            data_fim=self.agora + timedelta(minutes=1),
        )
        self.assertEqual(relatorio.receita_bruta, 220)
        self.assertEqual(relatorio.repasse_total, 132)
        self.assertEqual(relatorio.receita_bruta, self.painel().receita_periodo)
        self.assertEqual(relatorio.sessoes_realizadas, 1)

    def test_receita_fora_do_mes_nao_entra_no_painel(self):
        mes_anterior = self.agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        self.adicionar_receita("Receita mês anterior", 500, data=mes_anterior)
        self.assertEqual(self.painel().receita_periodo, 0)

    def test_sem_permissao_financeira_nao_expoe_valores(self):
        self.realizar()
        self.user.cargo = None
        self.db.commit()
        self.assertEqual(self.painel().receita_periodo, 0)
        self.assertEqual(self.painel().repasse_periodo, 0)


if __name__ == "__main__":
    unittest.main()
