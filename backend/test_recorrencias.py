"""AGE-04: reservas ilimitadas, exceções, versões e preservação em banco isolado."""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import recorrencias as regras
from app.database import Base
from app.models import (Agendamento, LancamentoFinanceiro, OcorrenciaRecorrencia, Paciente,
                        PerfilUsuario, Prontuario, Psicologo, Recorrencia, StatusAgendamento, Usuario)
from app.routers.agendamentos import criar_agendamento, atualizar_agendamento, reagendar_agendamento
from app.routers.recorrencias import listar
from app.schemas import (AgendamentoCreate, AgendamentoUpdate, ReagendamentoCreate,
                         RecorrenciaAlterar, RecorrenciaCreate, RecorrenciaEncerrar)


class RecorrenciasTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False)
        self.agora = datetime(2026, 10, 23, 12)
        self.clock = patch("app.horarios.agora_utc", return_value=self.agora)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.pacs = [Paciente(nome=f"Paciente fictício {i}") for i in range(2)]
        self.psis = [Psicologo(nome=f"Profissional fictício {i}", crp="teste", email=f"p{i}@example.com") for i in range(2)]
        self.user = Usuario(nome="Gestão fictícia", email="g@example.com", senha_hash="teste", perfil=PerfilUsuario.admin)
        self.db.add_all([*self.pacs, *self.psis, self.user])
        self.db.commit()
        self.inicio = datetime(2026, 10, 27, 21)  # terça-feira, 18h em Brasília

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def criar(self, dias=7, inicio=None, pac=0, psi=0, usuario=None):
        inicio = inicio or self.inicio
        return regras.criar(self.db, RecorrenciaCreate(paciente_id=self.pacs[pac].id,
                            psicologo_id=self.psis[psi].id, inicio=inicio,
                            fim=inicio + timedelta(minutes=50), intervalo_dias=dias), usuario or self.user)

    def avulso(self, inicio, pac=1, psi=0):
        return criar_agendamento(AgendamentoCreate(paciente_id=self.pacs[pac].id, psicologo_id=self.psis[psi].id,
                                 inicio=inicio, fim=inicio + timedelta(minutes=50)), self.db, self.user)

    def recusa(self, codigo, acao):
        with self.assertRaises(HTTPException) as erro:
            acao()
        self.assertEqual(erro.exception.status_code, codigo, erro.exception.detail)

    def sessoes(self, r):
        return self.db.query(Agendamento).join(OcorrenciaRecorrencia).filter(
            OcorrenciaRecorrencia.recorrencia_id == r.id).order_by(Agendamento.inicio).all()

    def status(self, ag, status):
        return atualizar_agendamento(ag.id, AgendamentoUpdate(status=status), self.db, self.user)

    def alterar(self, r, inicio, corte=None):
        return regras.alterar(self.db, r.id, RecorrenciaAlterar(a_partir_de=corte or self.inicio,
                              inicio=inicio, fim=inicio + timedelta(minutes=50), intervalo_dias=14,
                              motivo="Mudança solicitada"), self.user)

    def test_semanal_gera_90_dias_sem_faturar(self):
        r = self.criar()
        sessoes = self.sessoes(r)
        self.assertEqual(len(sessoes), 13)
        self.assertIsNone(r.encerrada_em)
        self.assertTrue(all(b.inicio - a.inicio == timedelta(days=7) for a, b in zip(sessoes, sessoes[1:])))
        self.assertEqual(regras.local(sessoes[-1].inicio).hour, 18)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 0)

    def test_quinzenal_a_cada_14_dias(self):
        sessoes = self.sessoes(self.criar(14))
        self.assertEqual(len(sessoes), 7)
        self.assertEqual(sessoes[1].inicio - sessoes[0].inicio, timedelta(days=14))

    def test_avulso_bloqueado_dez_anos_alem_do_horizonte(self):
        self.criar()
        self.recusa(409, lambda: self.avulso(self.inicio + timedelta(weeks=520)))

    def test_regra_recusa_avulso_futuro_fora_do_horizonte_sem_persistir_parcial(self):
        self.avulso(self.inicio + timedelta(weeks=70))
        self.recusa(409, self.criar)
        self.assertEqual(self.db.query(Recorrencia).count(), 0)
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_quinzenas_alternadas_podem_coexistir(self):
        self.criar(14)
        self.criar(14, inicio=self.inicio + timedelta(days=7), pac=1)
        self.assertEqual(self.db.query(Recorrencia).count(), 2)

    def test_semanal_conflita_com_quinzenal_futura(self):
        self.criar(14)
        self.recusa(409, lambda: self.criar(inicio=self.inicio + timedelta(weeks=40), pac=1))

    def test_bloqueia_paciente_em_outro_profissional(self):
        self.criar()
        self.recusa(409, lambda: self.criar(psi=1))

    def test_intervalos_adjacentes_permitidos(self):
        self.criar()
        self.criar(inicio=self.inicio + timedelta(minutes=50), pac=1)

    def test_cruzamento_da_meia_noite(self):
        inicio = datetime(2026, 10, 28, 2, 40)
        self.criar(inicio=inicio)
        self.recusa(409, lambda: self.avulso(inicio + timedelta(weeks=30, minutes=25)))

    def test_cancelar_somente_sessao_libera_excecao_e_nao_recria(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        self.status(ag, "cancelado")
        self.avulso(ag.inicio)
        self.assertEqual(regras.gerar_proximas(self.db, self.user), 0)
        self.recusa(409, lambda: self.avulso(self.inicio + timedelta(weeks=40)))

    def test_falta_nao_encerra_recorrencia(self):
        r = self.criar()
        self.status(self.sessoes(r)[0], "falta")
        self.recusa(409, lambda: self.avulso(self.inicio + timedelta(weeks=40)))

    def test_reagendamento_pontual_preserva_sequencia(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        novo = reagendar_agendamento(ag.id, ReagendamentoCreate(inicio=ag.inicio + timedelta(days=1),
                                    fim=ag.fim + timedelta(days=1)), self.db, self.user)
        self.assertNotEqual(novo.id, ag.id)
        self.assertEqual(self.sessoes(r)[0].status, StatusAgendamento.cancelado)
        self.recusa(409, lambda: self.avulso(self.inicio + timedelta(weeks=40)))

    def test_realizar_sessao_gera_somente_o_par_da_sessao(self):
        r = self.criar()
        self.status(self.sessoes(r)[0], "realizado")
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)
        self.assertEqual(self.db.query(Agendamento).filter_by(status=StatusAgendamento.realizado).count(), 1)

    def test_encerramento_libera_futuro_preserva_passado_e_prontuario(self):
        r = self.criar()
        primeira = self.sessoes(r)[0]
        self.status(primeira, "realizado")
        self.db.add(Prontuario(paciente_id=primeira.paciente_id, psicologo_id=primeira.psicologo_id,
                              agendamento_id=primeira.id, evolucao="Registro fictício"))
        self.db.commit()
        corte = self.inicio + timedelta(days=1)
        regras.encerrar(self.db, r.id, RecorrenciaEncerrar(a_partir_de=corte, motivo="Fim da reserva"), self.user)
        self.assertEqual(primeira.status, StatusAgendamento.realizado)
        self.assertEqual(self.db.query(Prontuario).count(), 1)
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)
        self.avulso(self.inicio + timedelta(weeks=40))
        self.recusa(409, lambda: self.status(self.sessoes(r)[1], "agendado"))
        self.assertEqual(r.encerrada_por_id, self.user.id)

    def test_nao_encerra_sobre_historico_futuro(self):
        r = self.criar()
        self.status(self.sessoes(r)[1], "realizado")
        self.recusa(409, lambda: regras.encerrar(self.db, r.id, RecorrenciaEncerrar(motivo="Teste"), self.user))
        self.assertIsNone(self.db.get(Recorrencia, r.id).encerrada_em)
        self.assertEqual(self.sessoes(r)[0].status, StatusAgendamento.agendado)

    def test_alterar_cria_versao_preserva_reservas_anteriores(self):
        r = self.criar()
        primeira = self.sessoes(r)[0]
        corte = self.inicio + timedelta(days=1)
        nova = self.alterar(r, self.inicio + timedelta(days=2), corte)
        self.assertEqual(nova.anterior_id, r.id)
        self.assertEqual(primeira.status, StatusAgendamento.agendado)
        self.assertEqual(self.sessoes(r)[1].status, StatusAgendamento.cancelado)
        self.recusa(409, lambda: self.avulso(nova.inicio + timedelta(weeks=40)))

    def test_mudanca_conflitante_faz_rollback_inclusive_cancelamentos(self):
        r = self.criar()
        nova_data = self.inicio + timedelta(days=1)
        self.avulso(nova_data)
        self.recusa(409, lambda: self.alterar(r, nova_data))
        self.assertIsNone(self.db.get(Recorrencia, r.id).encerrada_em)
        self.assertTrue(all(a.status == StatusAgendamento.agendado for a in self.sessoes(r)))
        self.assertEqual(self.db.query(Recorrencia).count(), 1)

    def test_geracao_idempotente_e_amplia_horizonte_sem_repetir(self):
        r = self.criar()
        self.assertEqual(regras.gerar_proximas(self.db, self.user), 0)
        with patch("app.horarios.agora_utc", return_value=self.agora + timedelta(days=60)):
            self.assertGreater(regras.gerar_proximas(self.db, self.user), 0)
            self.assertEqual(regras.gerar_proximas(self.db, self.user), 0)
        self.assertEqual(self.db.query(OcorrenciaRecorrencia).count(), len(self.sessoes(r)))

    def test_falha_na_geracao_desfaz_regra_e_sessoes(self):
        original = regras.validar_reserva
        chamadas = 0
        def falhar(*args, **kwargs):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 5:
                raise RuntimeError("Falha simulada")
            return original(*args, **kwargs)
        with patch("app.recorrencias.validar_reserva", side_effect=falhar), self.assertRaises(RuntimeError):
            self.criar()
        self.assertEqual(self.db.query(Recorrencia).count(), 0)
        self.assertEqual(self.db.query(Agendamento).count(), 0)

    def test_profissional_so_gerencia_a_propria_sequencia(self):
        psi = Usuario(nome="Profissional", email="u@example.com", senha_hash="teste", perfil=PerfilUsuario.psicologo,
                      psicologo_id=self.psis[0].id)
        self.db.add(psi)
        self.db.commit()
        self.db.add(Agendamento(paciente_id=self.pacs[0].id, psicologo_id=self.psis[0].id,
                    inicio=self.agora - timedelta(days=1), fim=self.agora - timedelta(days=1) + timedelta(minutes=50),
                    status=StatusAgendamento.cancelado))
        self.db.commit()
        propria = self.criar(usuario=psi)
        outra = self.criar(pac=1, psi=1)
        self.assertEqual([r.id for r in listar(self.db, psi)], [propria.id])
        self.recusa(403, lambda: regras.encerrar(self.db, outra.id, RecorrenciaEncerrar(motivo="Teste"), psi))
        self.recusa(403, lambda: self.criar(inicio=self.inicio + timedelta(days=1), psi=1, usuario=psi))

    def test_profissional_sem_vinculo_nao_lista_cria_ou_gera(self):
        psi = Usuario(nome="Sem vínculo", email="v@example.com", senha_hash="teste", perfil=PerfilUsuario.psicologo)
        self.db.add(psi)
        self.db.commit()
        self.recusa(403, lambda: listar(self.db, psi))
        self.recusa(403, lambda: self.criar(usuario=psi))
        self.recusa(403, lambda: regras.gerar_proximas(self.db, psi))

    def test_passado_e_duracao_invalida_recusados(self):
        self.recusa(422, lambda: self.criar(inicio=self.agora))
        for minutos in [0, -1, 1441]:
            self.recusa(422, lambda: regras.preparar_regra(self.pacs[0].id, self.psis[0].id, self.inicio,
                         self.inicio + timedelta(minutes=minutos), 7, self.user))

    def test_patch_nao_move_ocorrencia_sem_excecao(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        self.recusa(409, lambda: atualizar_agendamento(ag.id, AgendamentoUpdate(inicio=ag.inicio + timedelta(hours=1),
                    fim=ag.fim + timedelta(hours=1)), self.db, self.user))

    def test_get_nao_gera_sessoes(self):
        self.criar()
        antes = self.db.query(Agendamento).count()
        with patch("app.horarios.agora_utc", return_value=self.agora + timedelta(days=60)):
            listar(self.db, self.user)
        self.assertEqual(self.db.query(Agendamento).count(), antes)

    def test_encerrar_agora_com_relogio_avancando(self):
        r = self.criar()
        ticks = iter(self.agora + timedelta(microseconds=i) for i in range(100))
        with patch("app.horarios.agora_utc", side_effect=lambda: next(ticks)):
            regras.encerrar(self.db, r.id, RecorrenciaEncerrar(motivo="Fim"), self.user)
        self.assertIsNotNone(r.encerrada_em)

    def test_cadastro_inativo_nao_impede_encerramento(self):
        r = self.criar()
        self.pacs[0].ativo = False
        self.db.commit()
        self.assertEqual(regras.gerar_proximas(self.db, self.user), 0)
        regras.encerrar(self.db, r.id, RecorrenciaEncerrar(motivo="Fim"), self.user)
        self.assertIsNotNone(r.encerrada_em)

    def test_reserva_com_inicio_distante_nao_perde_primeira_sessao(self):
        r = self.criar(inicio=self.inicio + timedelta(weeks=100))
        self.assertEqual(self.sessoes(r)[0].inicio, r.inicio)
        self.recusa(409, lambda: self.avulso(r.inicio + timedelta(weeks=100)))

    def test_indice_impede_duplicar_ocorrencia_no_banco(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        self.db.add(OcorrenciaRecorrencia(recorrencia_id=r.id, inicio_original=ag.inicio, agendamento_id=ag.id))
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()

    def test_tabelas_novas_em_schema_existente_sem_alterar_agendamento(self):
        self.avulso(self.inicio + timedelta(days=1))
        def assinatura():
            return [(c["name"], str(c["type"]), c["nullable"], c["default"], c["primary_key"])
                    for c in inspect(self.engine).get_columns("agendamentos")]
        colunas_antes = assinatura()
        self.db.commit()
        with self.engine.begin() as conn:
            OcorrenciaRecorrencia.__table__.drop(conn)
            Recorrencia.__table__.drop(conn)
        Base.metadata.create_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.assertEqual(assinatura(), colunas_antes)
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_encerramento_futuro_preserva_reserva_ate_corte(self):
        r = self.criar()
        corte = self.inicio + timedelta(weeks=80)
        regras.encerrar(self.db, r.id, RecorrenciaEncerrar(a_partir_de=corte, motivo="Fim programado"), self.user)
        self.recusa(409, lambda: self.avulso(self.inicio + timedelta(weeks=79)))
        self.avulso(corte)

    def test_primeira_excecao_nao_esconde_conflito_das_proximas(self):
        r = self.criar()
        self.status(self.sessoes(r)[0], "cancelado")
        self.recusa(409, lambda: self.criar(pac=1))

    def test_reabertura_de_excecao_ocupada_recusada(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        self.status(ag, "cancelado")
        self.avulso(ag.inicio)
        self.recusa(409, lambda: self.status(ag, "agendado"))

    def test_encerramento_alcanca_cadeia_de_reagendamentos_pontuais(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        novo = reagendar_agendamento(ag.id, ReagendamentoCreate(inicio=ag.inicio + timedelta(days=1),
                                    fim=ag.fim + timedelta(days=1)), self.db, self.user)
        sucessor = reagendar_agendamento(novo.id, ReagendamentoCreate(inicio=ag.inicio + timedelta(days=2),
                                        fim=ag.fim + timedelta(days=2)), self.db, self.user)
        self.assertEqual(sucessor.recorrencia_id, r.id)
        regras.encerrar(self.db, r.id, RecorrenciaEncerrar(motivo="Fim"), self.user)
        self.assertEqual(self.db.get(Agendamento, sucessor.id).status, StatusAgendamento.cancelado)
        self.recusa(409, lambda: atualizar_agendamento(sucessor.id, AgendamentoUpdate(status="agendado"), self.db, self.user))

    def test_nao_reagenda_sessao_para_periodo_encerrado(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        regras.encerrar(self.db, r.id, RecorrenciaEncerrar(motivo="Fim"), self.user)
        self.recusa(409, lambda: reagendar_agendamento(ag.id, ReagendamentoCreate(inicio=ag.inicio + timedelta(days=1),
                    fim=ag.fim + timedelta(days=1)), self.db, self.user))

    def test_sessao_em_cache_nao_reabre_apos_encerramento_em_outra_sessao(self):
        r = self.criar()
        ag = self.sessoes(r)[0]
        self.assertIsNone(ag.ocorrencia.recorrencia.encerrada_em)
        with Session(self.engine, autoflush=False) as outra:
            regras.encerrar(outra, r.id, RecorrenciaEncerrar(motivo="Fim externo"), outra.get(Usuario, self.user.id))
        self.recusa(409, lambda: self.status(ag, "agendado"))


if __name__ == "__main__":
    unittest.main()
