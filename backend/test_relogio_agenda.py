"""Referência de horário da API e o caso de 19:50 já vencido."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.horarios import utc_sem_fuso
from app.models import StatusAgendamento
from app.routers.agendamentos import relogio_agenda
from app.validacao_agenda import validar_reserva


class RelogioAgendaTest(unittest.TestCase):
    def test_referencia_identifica_utc_explicitamente(self):
        with patch("app.horarios.agora_utc", return_value=datetime(2026, 10, 23, 22, 56)):
            dados = relogio_agenda(_=None)
        self.assertEqual(dados.agora.utcoffset(), timedelta(0))
        self.assertEqual(dados.agora.hour, 22)
        self.assertEqual(dados.fuso_horario, "America/Sao_Paulo")

    def test_referencia_avanca_com_o_relogio_real_da_api(self):
        with patch("app.horarios.agora_utc", side_effect=[datetime(2026, 10, 23, 22, 56), datetime(2026, 10, 23, 22, 57)]):
            antes = relogio_agenda(_=None).agora
            depois = relogio_agenda(_=None).agora
        self.assertEqual(depois - antes, timedelta(minutes=1))

    def test_19_50_em_brasilia_e_recusado_quando_agora_e_19_56(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db, patch("app.horarios.agora_utc", return_value=datetime(2026, 10, 23, 22, 56)):
                inicio = utc_sem_fuso(datetime.fromisoformat("2026-10-23T19:50:00-03:00"))
                with self.assertRaises(HTTPException) as erro:
                    validar_reserva(db, 1, 1, inicio, inicio + timedelta(minutes=50), StatusAgendamento.agendado, exigir_futuro=True)
                self.assertEqual(erro.exception.status_code, 422)
                self.assertIn("futuro", erro.exception.detail)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
