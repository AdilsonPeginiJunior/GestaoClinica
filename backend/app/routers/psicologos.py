"""Profissionais e percentual de repasse usado no fechamento financeiro."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_perfis
from app.database import get_db
from app.models import PerfilUsuario, Psicologo, Usuario
from app.schemas import PsicologoCreate, PsicologoRead, PsicologoUpdate

router = APIRouter(prefix="/api/psicologos", tags=["psicologos"])


@router.get("", response_model=list[PsicologoRead])
def listar_psicologos(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return db.query(Psicologo).order_by(Psicologo.nome).all()


@router.post("", response_model=PsicologoRead, status_code=status.HTTP_201_CREATED)
def criar_psicologo(
    payload: PsicologoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_perfis(PerfilUsuario.admin, PerfilUsuario.socia)),
):
    psicologo = Psicologo(**payload.model_dump())
    db.add(psicologo)
    db.commit()
    db.refresh(psicologo)
    return psicologo


@router.get("/{psicologo_id}", response_model=PsicologoRead)
def obter_psicologo(psicologo_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    psicologo = db.get(Psicologo, psicologo_id)
    if not psicologo:
        raise HTTPException(status_code=404, detail="Psicologo nao encontrado")
    return psicologo


@router.patch("/{psicologo_id}", response_model=PsicologoRead)
def atualizar_psicologo(
    psicologo_id: int,
    payload: PsicologoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_perfis(PerfilUsuario.admin, PerfilUsuario.socia)),
):
    psicologo = db.get(Psicologo, psicologo_id)
    if not psicologo:
        raise HTTPException(status_code=404, detail="Psicologo nao encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(psicologo, key, value)
    db.commit()
    db.refresh(psicologo)
    return psicologo
