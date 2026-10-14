"""Cadastro de pacientes (dados administrativos — sem prontuario neste prototipo."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_permission
from app.database import get_db
from app.models import Paciente, Usuario
from app.schemas import PacienteCreate, PacienteRead, PacienteUpdate

router = APIRouter(prefix="/api/pacientes", tags=["pacientes"])


@router.get("", response_model=list[PacienteRead])
def listar_pacientes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("pacientes:consultar")),
    q: str | None = Query(None),
    ativo: bool | None = Query(None),
):
    query = db.query(Paciente)
    if q:
        like = f"%{q}%"
        query = query.filter(Paciente.nome.ilike(like))
    if ativo is not None:
        query = query.filter(Paciente.ativo == ativo)
    return query.order_by(Paciente.nome).all()


@router.post("", response_model=PacienteRead, status_code=status.HTTP_201_CREATED)
def criar_paciente(
    payload: PacienteCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("pacientes:gerenciar")),
):
    paciente = Paciente(**payload.model_dump())
    db.add(paciente)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF ja cadastrado ou dado duplicado.",
        ) from exc
    db.refresh(paciente)
    return paciente


@router.get("/{paciente_id}", response_model=PacienteRead)
def obter_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("pacientes:consultar")),
):
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente nao encontrado")
    return paciente


@router.patch("/{paciente_id}", response_model=PacienteRead)
def atualizar_paciente(
    paciente_id: int,
    payload: PacienteUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("pacientes:gerenciar")),
):
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(paciente, key, value)
    db.commit()
    db.refresh(paciente)
    return paciente
