"""Disponibilidade e integridade da reserva de profissional e paciente."""

from fastapi import HTTPException
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app.horarios import utc_sem_fuso
from app import horarios
from app.models import Agendamento, Paciente, Psicologo, StatusAgendamento


STATUS_QUE_OCUPAM_HORARIO = {
    StatusAgendamento.agendado, StatusAgendamento.confirmado, StatusAgendamento.realizado,
}
CAMPOS_DA_RESERVA = {"paciente_id", "psicologo_id", "inicio", "fim"}


def normalizar_horarios(dados: dict) -> dict:
    dados = dados.copy()
    for campo in ("inicio", "fim"):
        if dados.get(campo) is not None:
            try:
                dados[campo] = utc_sem_fuso(dados[campo])
            except (OverflowError, ValueError) as exc:
                raise HTTPException(status_code=422, detail="Data ou horário fora do intervalo permitido.") from exc
    return dados


def validar_reserva(
    db: Session, paciente_id: int, psicologo_id: int, inicio, fim,
    status: StatusAgendamento, ignorar_agendamento_id: int | None = None, exigir_futuro: bool = False,
    ignorar_recorrencia_id: int | None = None,
) -> None:
    """Trava os recursos e valida a reserva dentro da transação chamadora.

    Ordem fixa: profissional, depois paciente. UPDATE do campo não-chave ativo
    serializa reservas do mesmo recurso, inclusive quando ainda não existe
    atendimento para travar. Nenhum valor cadastral é alterado.
    """
    if fim <= inicio:
        raise HTTPException(status_code=422, detail="O horário final deve ser posterior ao horário inicial.")
    if exigir_futuro and inicio <= horarios.agora_utc():
        raise HTTPException(status_code=422, detail="Escolha uma data e um horário no futuro.")
    with db.no_autoflush:
        for modelo, identificador, nome in (
            (Psicologo, psicologo_id, "Profissional"),
            (Paciente, paciente_id, "Paciente"),
        ):
            resultado = db.execute(
                update(modelo).where(modelo.id == identificador)
                .values(ativo=modelo.ativo).execution_options(synchronize_session=False)
            )
            if resultado.rowcount != 1:
                raise HTTPException(status_code=422, detail=f"{nome} não encontrado.")
            # Consulta só o atributo ativo, sem confiar no cache da sessão nem
            # sobrescrever outros atributos pendentes na unidade de trabalho.
            ativo = db.query(modelo.ativo).filter(modelo.id == identificador).scalar()
            if not ativo:
                raise HTTPException(status_code=409, detail=f"{nome} inativo. Reative o cadastro antes de agendar.")

        # O horário pode ter vencido enquanto a operação aguardava as travas.
        if exigir_futuro and inicio <= horarios.agora_utc():
            raise HTTPException(status_code=422, detail="Escolha uma data e um horário no futuro.")
        if status not in STATUS_QUE_OCUPAM_HORARIO:
            return
        query = db.query(Agendamento.psicologo_id, Agendamento.paciente_id).filter(
            Agendamento.status.in_(STATUS_QUE_OCUPAM_HORARIO),
            Agendamento.inicio < fim,
            Agendamento.fim > inicio,
            or_(Agendamento.psicologo_id == psicologo_id, Agendamento.paciente_id == paciente_id),
        )
        if ignorar_agendamento_id is not None:
            query = query.filter(Agendamento.id != ignorar_agendamento_id)
        conflito = query.first()
        if conflito:
            if conflito.psicologo_id == psicologo_id:
                raise HTTPException(status_code=409, detail="O profissional já possui atendimento nesse horário.")
            raise HTTPException(status_code=409, detail="O paciente já possui atendimento nesse horário.")
        from app.recorrencias import validar_conflito_recorrencias
        validar_conflito_recorrencias(db, paciente_id, psicologo_id, inicio, fim,
                                     ignorar_agendamento_id, ignorar_recorrencia_id)
