"""Cadastro de pacientes (dados administrativos — sem prontuario neste prototipo."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_permission
from app.database import get_db
from app.models import Paciente, PerfilUsuario, Usuario
from app.escopo import filtrar_pacientes
from app.transacoes import transacao
from app.schemas import PacienteCreate, PacienteRead, PacienteUpdate

router = APIRouter(prefix="/api/pacientes", tags=["pacientes"])


@router.get("", response_model=list[PacienteRead])
def listar_pacientes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("pacientes:consultar")),
    q: str | None = Query(None),
    ativo: bool | None = Query(None),
):
    query = filtrar_pacientes(db.query(Paciente), _)
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
    if _.perfil == PerfilUsuario.psicologo:
        raise HTTPException(403, "Novos pacientes devem ser cadastrados e direcionados pela recepção ou gestão.")
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
    paciente = filtrar_pacientes(db.query(Paciente), _).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


@router.patch("/{paciente_id}", response_model=PacienteRead)
def atualizar_paciente(
    paciente_id: int,
    payload: PacienteUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("pacientes:gerenciar")),
):
    with transacao(db):
        resultado = db.execute(update(Paciente).where(Paciente.id == paciente_id).values(ativo=Paciente.ativo)
                               .execution_options(synchronize_session=False))
        if resultado.rowcount != 1:
            raise HTTPException(404, "Paciente não encontrado.")
        # Mesmo bloqueio de paciente usado ao transferir/agendar uma reserva.
        # Revalida o escopo após obtê-lo, sem confiar em cadastro já em cache.
        paciente = filtrar_pacientes(db.query(Paciente), _).filter(Paciente.id == paciente_id).populate_existing().first()
        if paciente is None:
            raise HTTPException(404, "Paciente não encontrado.")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(paciente, key, value)
    db.refresh(paciente)
    return paciente
