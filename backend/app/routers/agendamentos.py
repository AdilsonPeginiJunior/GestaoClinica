"""
Endpoints de agendamento — nucleo operacional da recepcao.

Ao mudar status para 'realizado', services.aplicar_status_agendamento
dispara lancamentos financeiros automaticos.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, require_perfis
from app.database import get_db
from app.models import Agendamento, PerfilUsuario, StatusAgendamento, Usuario
from app.schemas import AgendamentoCreate, AgendamentoRead, AgendamentoUpdate
from app.services import aplicar_status_agendamento

router = APIRouter(prefix="/api/agendamentos", tags=["agendamentos"])


def _serialize(ag: Agendamento) -> AgendamentoRead:
    return AgendamentoRead(
        id=ag.id,
        paciente_id=ag.paciente_id,
        psicologo_id=ag.psicologo_id,
        inicio=ag.inicio,
        fim=ag.fim,
        status=ag.status,
        observacoes=ag.observacoes,
        criado_em=ag.criado_em,
        paciente_nome=ag.paciente.nome if ag.paciente else None,
        psicologo_nome=ag.psicologo.nome if ag.psicologo else None,
    )


@router.get("", response_model=list[AgendamentoRead])
def listar_agendamentos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    data_inicio: datetime | None = Query(None),
    data_fim: datetime | None = Query(None),
    psicologo_id: int | None = Query(None),
    status_filtro: StatusAgendamento | None = Query(None, alias="status"),
):
    query = db.query(Agendamento).options(joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo))
    if current_user.perfil == PerfilUsuario.psicologo and current_user.psicologo_id:
        query = query.filter(Agendamento.psicologo_id == current_user.psicologo_id)
    elif psicologo_id is not None:
        query = query.filter(Agendamento.psicologo_id == psicologo_id)
    if data_inicio:
        query = query.filter(Agendamento.inicio >= data_inicio)
    if data_fim:
        query = query.filter(Agendamento.inicio <= data_fim)
    if status_filtro:
        query = query.filter(Agendamento.status == status_filtro)
    items = query.order_by(Agendamento.inicio).all()
    return [_serialize(a) for a in items]


@router.post("", response_model=AgendamentoRead, status_code=status.HTTP_201_CREATED)
def criar_agendamento(
    payload: AgendamentoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_perfis(PerfilUsuario.recepcionista, PerfilUsuario.admin, PerfilUsuario.socia, PerfilUsuario.psicologo)),
):
    ag = Agendamento(**payload.model_dump())
    db.add(ag)
    db.commit()
    db.refresh(ag)
    ag = (
        db.query(Agendamento)
        .options(joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo))
        .filter(Agendamento.id == ag.id)
        .first()
    )
    if ag.status == StatusAgendamento.realizado:
        aplicar_status_agendamento(db, ag, StatusAgendamento.realizado)
    return _serialize(ag)


@router.patch("/{agendamento_id}", response_model=AgendamentoRead)
def atualizar_agendamento(
    agendamento_id: int,
    payload: AgendamentoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ag = (
        db.query(Agendamento)
        .options(joinedload(Agendamento.paciente), joinedload(Agendamento.psicologo))
        .filter(Agendamento.id == agendamento_id)
        .first()
    )
    if not ag:
        raise HTTPException(status_code=404, detail="Agendamento nao encontrado")
    if current_user.perfil == PerfilUsuario.psicologo and current_user.psicologo_id != ag.psicologo_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    data = payload.model_dump(exclude_unset=True)
    novo_status = data.pop("status", None)
    for key, value in data.items():
        setattr(ag, key, value)
    db.commit()
    db.refresh(ag)

    if novo_status is not None:
        aplicar_status_agendamento(db, ag, novo_status)
        db.refresh(ag)

    return _serialize(ag)
