"""Registro de evolucoes clinicas vinculadas a consultas realizadas."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import has_permission, require_permission
from app.database import get_db
from app.models import Agendamento, Prontuario, StatusAgendamento, Usuario
from app.schemas import AgendamentoRead, ProntuarioCreate, ProntuarioRead

router = APIRouter(prefix="/api/prontuario", tags=["prontuario"])


def _serialize(record: Prontuario) -> ProntuarioRead:
    return ProntuarioRead(
        id=record.id,
        paciente_id=record.paciente_id,
        paciente_nome=record.paciente.nome,
        agendamento_id=record.agendamento_id,
        psicologo_id=record.psicologo_id,
        psicologo_nome=record.psicologo.nome,
        evolucao=record.evolucao,
        criado_em=record.criado_em,
    )


def _serialize_agendamento(appointment: Agendamento) -> AgendamentoRead:
    return AgendamentoRead(
        id=appointment.id,
        paciente_id=appointment.paciente_id,
        psicologo_id=appointment.psicologo_id,
        inicio=appointment.inicio,
        fim=appointment.fim,
        status=appointment.status,
        observacoes=appointment.observacoes,
        criado_em=appointment.criado_em,
        paciente_nome=appointment.paciente.nome,
        psicologo_nome=appointment.psicologo.nome,
    )


@router.get("/atendimentos-disponiveis", response_model=list[AgendamentoRead])
def atendimentos_disponiveis(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("prontuario:criar")),
):
    if not user.psicologo_id:
        raise HTTPException(status_code=403, detail="Usuario sem psicologo vinculado.")
    appointments = (
        db.query(Agendamento)
        .options(joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo))
        .outerjoin(Prontuario, Prontuario.agendamento_id == Agendamento.id)
        .filter(
            Agendamento.psicologo_id == user.psicologo_id,
            Agendamento.status == StatusAgendamento.realizado,
            Prontuario.id.is_(None),
        )
        .order_by(Agendamento.inicio.desc())
        .all()
    )
    return [_serialize_agendamento(appointment) for appointment in appointments]


@router.get("", response_model=list[ProntuarioRead])
def listar_prontuarios(
    db: Session = Depends(get_db),
    user: Usuario = Depends(
        require_permission("prontuario:ler_proprio", "prontuario:ler_todos")
    ),
):
    query = db.query(Prontuario).options(
        joinedload(Prontuario.paciente), joinedload(Prontuario.psicologo)
    )
    if not has_permission(user, "prontuario:ler_todos"):
        if not user.psicologo_id:
            raise HTTPException(status_code=403, detail="Usuario sem psicologo vinculado.")
        query = query.filter(Prontuario.psicologo_id == user.psicologo_id)
    records = query.order_by(Prontuario.criado_em.desc()).all()
    return [_serialize(record) for record in records]


@router.post("", response_model=ProntuarioRead, status_code=status.HTTP_201_CREATED)
def criar_evolucao(
    payload: ProntuarioCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("prontuario:criar")),
):
    if not user.psicologo_id:
        raise HTTPException(status_code=403, detail="Usuario sem psicologo vinculado.")
    appointment = db.get(Agendamento, payload.agendamento_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Atendimento nao encontrado.")
    if appointment.psicologo_id != user.psicologo_id:
        raise HTTPException(status_code=403, detail="Acesso negado a este atendimento.")
    if appointment.status != StatusAgendamento.realizado:
        raise HTTPException(status_code=409, detail="So e possivel registrar evolucao em atendimento realizado.")
    if db.query(Prontuario).filter(Prontuario.agendamento_id == appointment.id).first():
        raise HTTPException(status_code=409, detail="Este atendimento ja possui evolucao registrada.")

    record = Prontuario(
        paciente_id=appointment.paciente_id,
        agendamento_id=appointment.id,
        psicologo_id=user.psicologo_id,
        evolucao=payload.evolucao.strip(),
    )
    if not record.evolucao:
        raise HTTPException(status_code=422, detail="A evolucao nao pode ficar vazia.")
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este atendimento ja possui evolucao registrada.") from exc
    record = (
        db.query(Prontuario)
        .options(joinedload(Prontuario.paciente), joinedload(Prontuario.psicologo))
        .filter(Prontuario.id == record.id)
        .one()
    )
    return _serialize(record)
