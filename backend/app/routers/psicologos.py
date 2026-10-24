"""Profissionais e percentual de repasse usado no fechamento financeiro."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import has_permission, require_permission
from app.database import get_db
from app.escopo import profissional_restrito
from app.models import Psicologo, Usuario
from app.schemas import PsicologoCreate, PsicologoRead, PsicologoUpdate

router = APIRouter(prefix="/api/psicologos", tags=["psicologos"])


@router.get("", response_model=list[PsicologoRead])
def listar_psicologos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("psicologos:consultar")),
):
    query = db.query(Psicologo)
    pid = profissional_restrito(_)
    if pid is not None and not has_permission(_, "relatorios:consultar_todos"):
        query = query.filter(Psicologo.id == pid)
    return query.order_by(Psicologo.nome).all()


@router.post("", response_model=PsicologoRead, status_code=status.HTTP_201_CREATED)
def criar_psicologo(
    payload: PsicologoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("psicologos:gerenciar")),
):
    if profissional_restrito(_) is not None:
        raise HTTPException(403, "Cadastro de profissionais é exclusivo da gestão autorizada.")
    psicologo = Psicologo(**payload.model_dump())
    db.add(psicologo)
    db.commit()
    db.refresh(psicologo)
    return psicologo


@router.get("/{psicologo_id}", response_model=PsicologoRead)
def obter_psicologo(
    psicologo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("psicologos:consultar")),
):
    pid = profissional_restrito(_)
    if pid is not None and pid != psicologo_id and not has_permission(_, "relatorios:consultar_todos"):
        raise HTTPException(404, "Profissional não encontrado.")
    psicologo = db.get(Psicologo, psicologo_id)
    if not psicologo:
        raise HTTPException(status_code=404, detail="Psicologo nao encontrado")
    return psicologo


@router.patch("/{psicologo_id}", response_model=PsicologoRead)
def atualizar_psicologo(
    psicologo_id: int,
    payload: PsicologoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("psicologos:gerenciar")),
):
    if profissional_restrito(_) is not None:
        raise HTTPException(403, "Cadastro e percentual de repasse são exclusivos da gestão autorizada.")
    psicologo = db.get(Psicologo, psicologo_id)
    if not psicologo:
        raise HTTPException(status_code=404, detail="Psicologo nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(psicologo, key, value)
    db.commit()
    db.refresh(psicologo)
    return psicologo
