"""Validações de horários e vínculos, em banco isolado."""

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Agendamento, Paciente, PerfilUsuario, Psicologo, StatusAgendamento, Usuario
from app.routers.agendamentos import atualizar_agendamento, criar_agendamento, listar_agendamentos
from app.schemas import AgendamentoCreate, AgendamentoUpdate


class AgendaTest(unittest.TestCase):
    def setUp(self):
        self.relogio = patch("app.horarios.agora_utc", return_value=datetime(2026, 10, 22))
        self.relogio.start()
        self.addCleanup(self.relogio.stop)
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False)
        self.pacientes = [Paciente(nome=f"Paciente fictício {i}") for i in range(2)]
        self.psicologos = [Psicologo(nome=f"Profissional fictício {i}", crp=f"teste-{i}", email=f"psi{i}@example.com") for i in range(2)]
        self.user = Usuario(nome="Gestão fictícia", email="gestao@example.com", senha_hash="nao-utilizado", perfil=PerfilUsuario.admin)
        self.db.add_all([*self.pacientes, *self.psicologos, self.user])
        self.db.commit()
        self.inicio = datetime(2026, 10, 23, 10)
        self.fim = self.inicio + timedelta(minutes=50)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def criar(self, **alteracoes):
        dados = dict(paciente_id=self.pacientes[0].id, psicologo_id=self.psicologos[0].id,
                     inicio=self.inicio, fim=self.fim)
        dados.update(alteracoes)
        return criar_agendamento(AgendamentoCreate(**dados), self.db, self.user)

    def atualizar(self, ag_id, **alteracoes):
        return atualizar_agendamento(ag_id, AgendamentoUpdate(**alteracoes), self.db, self.user)

    def afirmar_recusa(self, codigo, acao):
        with self.assertRaises(HTTPException) as erro:
            acao()
        self.assertEqual(erro.exception.status_code, codigo)

    def test_criacao_recusa_fim_igual_ou_anterior(self):
        for fim in [self.inicio, self.inicio - timedelta(minutes=1)]:
            with self.subTest(fim=fim):
                self.afirmar_recusa(422, lambda: self.criar(fim=fim))
        self.assertEqual(self.db.query(Agendamento).count(), 0)

    def test_paciente_inexistente(self):
        self.afirmar_recusa(422, lambda: self.criar(paciente_id=999))
        self.assertEqual(self.db.query(Agendamento).count(), 0)

    def test_profissional_inexistente(self):
        self.afirmar_recusa(422, lambda: self.criar(psicologo_id=999))
        self.assertEqual(self.db.query(Agendamento).count(), 0)

    def test_paciente_inativo(self):
        self.pacientes[0].ativo = False
        self.db.commit()
        self.afirmar_recusa(409, self.criar)

    def test_profissional_inativo(self):
        self.psicologos[0].ativo = False
        self.db.commit()
        self.afirmar_recusa(409, self.criar)

    def test_sobreposicoes_do_profissional_com_outro_paciente(self):
        self.criar()
        intervalos = [
            (self.inicio, self.fim),
            (self.inicio - timedelta(minutes=10), self.inicio + timedelta(minutes=10)),
            (self.inicio + timedelta(minutes=10), self.fim + timedelta(minutes=10)),
            (self.inicio + timedelta(minutes=10), self.fim - timedelta(minutes=10)),
            (self.inicio - timedelta(minutes=10), self.fim + timedelta(minutes=10)),
        ]
        for inicio, fim in intervalos:
            with self.subTest(inicio=inicio, fim=fim):
                self.afirmar_recusa(409, lambda: self.criar(paciente_id=self.pacientes[1].id, inicio=inicio, fim=fim))
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_sobreposicao_do_paciente_com_outro_profissional(self):
        self.criar()
        self.afirmar_recusa(409, lambda: self.criar(psicologo_id=self.psicologos[1].id))

    def test_intervalos_adjacentes_sao_permitidos(self):
        self.criar()
        self.criar(inicio=self.inicio - timedelta(minutes=50), fim=self.inicio)
        self.criar(inicio=self.fim, fim=self.fim + timedelta(minutes=50))
        self.assertEqual(self.db.query(Agendamento).count(), 3)

    def test_profissional_e_paciente_diferentes_podem_compartilhar_horario(self):
        self.criar()
        self.criar(paciente_id=self.pacientes[1].id, psicologo_id=self.psicologos[1].id)
        self.assertEqual(self.db.query(Agendamento).count(), 2)

    def test_cancelado_e_falta_nao_bloqueiam_horario(self):
        self.criar(status="cancelado")
        self.criar(status="falta")
        self.criar()
        self.assertEqual(self.db.query(Agendamento).count(), 3)

    def test_confirmado_e_realizado_bloqueiam_horario(self):
        for status in ["confirmado", "realizado"]:
            with self.subTest(status=status):
                ag = self.criar(status=status)
                self.afirmar_recusa(409, lambda: self.criar(paciente_id=self.pacientes[1].id))
                # Próximo cenário em outro horário, sem alterar histórico financeiro.
                self.inicio += timedelta(hours=2)
                self.fim += timedelta(hours=2)
                self.assertIsNotNone(ag.id)

    def test_patch_parcial_valida_intervalo_final_e_desfaz_outros_campos(self):
        ag = self.criar()
        self.afirmar_recusa(422, lambda: self.atualizar(ag.id, fim=self.inicio, observacoes="Não persistir"))
        self.afirmar_recusa(422, lambda: self.atualizar(ag.id, inicio=self.fim))
        armazenado = self.db.get(Agendamento, ag.id)
        self.assertEqual((armazenado.inicio, armazenado.fim), (self.inicio, self.fim))
        self.assertIsNone(armazenado.observacoes)

    def test_edicao_exclui_o_proprio_atendimento_da_busca(self):
        ag = self.criar()
        resposta = self.atualizar(ag.id, inicio=self.inicio, fim=self.fim, status="confirmado")
        self.assertEqual(resposta.status, StatusAgendamento.confirmado)

    def test_reagendamento_recusa_conflito_e_mantem_horario_anterior(self):
        self.criar()
        outro_inicio, outro_fim = self.inicio + timedelta(hours=2), self.fim + timedelta(hours=2)
        outro = self.criar(paciente_id=self.pacientes[1].id, inicio=outro_inicio, fim=outro_fim)
        self.afirmar_recusa(409, lambda: self.atualizar(outro.id, inicio=self.inicio, fim=self.fim))
        self.assertEqual(self.db.get(Agendamento, outro.id).inicio, outro_inicio)

    def test_reabrir_cancelado_recusa_horario_ocupado(self):
        cancelado = self.criar(status="cancelado")
        self.criar()
        self.afirmar_recusa(409, lambda: self.atualizar(cancelado.id, status="agendado"))
        self.assertEqual(self.db.get(Agendamento, cancelado.id).status, StatusAgendamento.cancelado)

    def test_troca_de_paciente_valida_disponibilidade(self):
        self.criar()
        outro = self.criar(paciente_id=self.pacientes[1].id, psicologo_id=self.psicologos[1].id)
        self.afirmar_recusa(409, lambda: self.atualizar(outro.id, paciente_id=self.pacientes[0].id))

    def test_troca_de_profissional_valida_disponibilidade(self):
        self.criar()
        outro = self.criar(paciente_id=self.pacientes[1].id, psicologo_id=self.psicologos[1].id)
        self.afirmar_recusa(409, lambda: self.atualizar(outro.id, psicologo_id=self.psicologos[0].id))

    def test_edicao_recusa_vinculo_inexistente(self):
        ag = self.criar()
        for campo in ["paciente_id", "psicologo_id"]:
            with self.subTest(campo=campo):
                self.afirmar_recusa(422, lambda: self.atualizar(ag.id, **{campo: 999}))

    def test_cancelar_com_cadastros_inativos_continua_permitido(self):
        ag = self.criar()
        self.pacientes[0].ativo = False
        self.psicologos[0].ativo = False
        self.db.commit()
        self.atualizar(ag.id, status="cancelado")
        self.afirmar_recusa(409, lambda: self.atualizar(ag.id, status="agendado"))

    def test_instantes_com_offsets_diferentes_sao_comparados_em_utc(self):
        self.criar(inicio="2026-10-23T10:00:00-03:00", fim="2026-10-23T10:50:00-03:00")
        self.afirmar_recusa(409, lambda: self.criar(inicio="2026-10-23T13:00:00Z", fim="2026-10-23T13:50:00Z"))
        ag = self.db.query(Agendamento).one()
        self.assertEqual(ag.inicio, datetime(2026, 10, 23, 13))

    def test_resposta_da_agenda_identifica_utc_para_exibicao_local(self):
        resposta = self.criar(inicio="2026-10-23T10:00:00-03:00", fim="2026-10-23T10:50:00-03:00")
        self.assertIsNotNone(resposta.inicio.tzinfo)
        self.assertEqual(resposta.inicio.utcoffset(), timedelta(0))
        self.assertEqual(resposta.inicio, datetime(2026, 10, 23, 13, tzinfo=timezone.utc))

    def test_ids_nao_positivos_sao_recusados_nos_schemas(self):
        for campo in ["paciente_id", "psicologo_id"]:
            for valor in [0, -1]:
                with self.subTest(campo=campo, valor=valor):
                    with self.assertRaises(ValidationError):
                        AgendamentoUpdate(**{campo: valor})
                    dados = dict(paciente_id=self.pacientes[0].id, psicologo_id=self.psicologos[0].id,
                                 inicio=self.inicio, fim=self.fim)
                    dados[campo] = valor
                    with self.assertRaises(ValidationError):
                        AgendamentoCreate(**dados)

    def test_intervalo_e_comparado_apos_converter_os_dois_offsets(self):
        self.afirmar_recusa(422, lambda: self.criar(inicio="2026-10-23T10:00:00-03:00", fim="2026-10-23T12:00:00Z"))

    def test_atendimento_pode_atravessar_meia_noite(self):
        self.criar(inicio="2026-10-23T23:40:00Z", fim="2026-10-24T00:30:00Z")
        self.assertEqual(self.db.query(Agendamento).count(), 1)

    def test_falta_reabre_somente_se_o_horario_estiver_livre(self):
        falta = self.criar(status="falta")
        self.criar()
        self.afirmar_recusa(409, lambda: self.atualizar(falta.id, status="agendado"))
        self.assertEqual(self.db.get(Agendamento, falta.id).status, StatusAgendamento.falta)

    def test_confirmacao_e_reagendamento_exigem_cadastro_ativo(self):
        ag = self.criar()
        self.psicologos[0].ativo = False
        self.db.commit()
        self.afirmar_recusa(409, lambda: self.atualizar(ag.id, status="confirmado"))
        self.afirmar_recusa(409, lambda: self.atualizar(ag.id, inicio=self.inicio + timedelta(minutes=10)))
        # Não se perde o histórico nem a possibilidade de encerrar como falta.
        self.atualizar(ag.id, observacoes="Manutenção textual")
        self.atualizar(ag.id, status="falta")

    def test_realizado_repetido_nao_exige_reativar_cadastro_historico(self):
        ag = self.criar(status="realizado")
        self.pacientes[0].ativo = False
        self.psicologos[0].ativo = False
        self.db.commit()
        self.atualizar(ag.id, status="realizado")
        from app.models import LancamentoFinanceiro
        self.assertEqual(self.db.query(LancamentoFinanceiro).count(), 2)

    def test_legado_com_intervalo_invalido_pode_ser_cancelado(self):
        ag = Agendamento(paciente_id=self.pacientes[0].id, psicologo_id=self.psicologos[0].id,
                         inicio=self.fim, fim=self.inicio, status=StatusAgendamento.agendado)
        self.db.add(ag)
        self.db.commit()
        self.atualizar(ag.id, status="cancelado")
        self.assertEqual(ag.status, StatusAgendamento.cancelado)

    def test_patch_parcial_com_offset_utiliza_os_campos_armazenados_em_utc(self):
        ag = self.criar(inicio="2026-10-23T10:00:00-03:00", fim="2026-10-23T10:50:00-03:00")
        self.afirmar_recusa(422, lambda: self.atualizar(ag.id, fim="2026-10-23T09:50:00-03:00"))
        self.atualizar(ag.id, fim="2026-10-23T11:00:00-03:00")
        self.assertEqual(self.db.get(Agendamento, ag.id).fim, datetime(2026, 10, 23, 14))

    def test_filtro_da_listagem_aceita_offset_sem_deslocar_periodo(self):
        self.criar(inicio="2026-10-23T10:00:00-03:00", fim="2026-10-23T10:50:00-03:00")
        itens = listar_agendamentos(
            db=self.db, current_user=self.user,
            data_inicio=datetime.fromisoformat("2026-10-23T09:59:00-03:00"),
            data_fim=datetime.fromisoformat("2026-10-23T10:01:00-03:00"),
            psicologo_id=None, status_filtro=None,
        )
        self.assertEqual(len(itens), 1)


if __name__ == "__main__":
    unittest.main()
