"""Administracao de cargos e atribuicao de permissoes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import require_perfis
from app.database import get_db
from app.models import Cargo, PerfilUsuario, Permissao, Usuario
from app.schemas import (
    CargoCreate,
    CargoRead,
    CargoUpdate,
    PermissaoRead,
    UsuarioCargoRead,
    UsuarioCargoUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["administracao"])
admin_only = require_perfis(PerfilUsuario.admin)


def _resolve_permissions(db: Session, permission_ids: list[int]) -> list[Permissao]:
    permissions = db.query(Permissao).filter(Permissao.id.in_(permission_ids)).all()
    if len(permissions) != len(set(permission_ids)):
        raise HTTPException(status_code=422, detail="Uma ou mais permissoes nao existem.")
    return permissions


@router.get("/permissoes", response_model=list[PermissaoRead])
def listar_permissoes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    return db.query(Permissao).order_by(Permissao.nome).all()


@router.get("/cargos", response_model=list[CargoRead])
def listar_cargos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    return (
        db.query(Cargo)
        .options(joinedload(Cargo.permissoes))
        .order_by(Cargo.nome)
        .all()
    )


@router.post("/cargos", response_model=CargoRead, status_code=status.HTTP_201_CREATED)
def criar_cargo(
    payload: CargoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    cargo = Cargo(
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        permissoes=_resolve_permissions(db, payload.permissao_ids),
    )
    db.add(cargo)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ja existe um cargo com esse nome.") from exc
    db.refresh(cargo)
    return cargo


@router.patch("/cargos/{cargo_id}", response_model=CargoRead)
def atualizar_cargo(
    cargo_id: int,
    payload: CargoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    cargo = (
        db.query(Cargo)
        .options(joinedload(Cargo.permissoes))
        .filter(Cargo.id == cargo_id)
        .first()
    )
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo nao encontrado.")
    data = payload.model_dump(exclude_unset=True)
    if "permissao_ids" in data:
        cargo.permissoes = _resolve_permissions(db, data.pop("permissao_ids") or [])
    if "nome" in data:
        cargo.nome = data["nome"].strip()
    if "descricao" in data:
        cargo.descricao = data["descricao"]
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ja existe um cargo com esse nome.") from exc
    db.refresh(cargo)
    return cargo


@router.delete("/cargos/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    cargo = db.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo nao encontrado.")
    if db.query(Usuario).filter(Usuario.cargo_id == cargo_id).first():
        raise HTTPException(status_code=409, detail="Reatribua os usuarios antes de excluir o cargo.")
    db.delete(cargo)
    db.commit()


@router.get("/usuarios", response_model=list[UsuarioCargoRead])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    users = db.query(Usuario).options(joinedload(Usuario.cargo)).order_by(Usuario.nome).all()
    return [
        UsuarioCargoRead(
            id=user.id,
            nome=user.nome,
            email=user.email,
            perfil=user.perfil,
            cargo_id=user.cargo_id,
            cargo_nome=user.cargo.nome if user.cargo else None,
        )
        for user in users
    ]


@router.patch("/usuarios/{usuario_id}/cargo", response_model=UsuarioCargoRead)
def atribuir_cargo(
    usuario_id: int,
    payload: UsuarioCargoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    user = db.query(Usuario).options(joinedload(Usuario.cargo)).filter(Usuario.id == usuario_id).first()
    cargo = db.get(Cargo, payload.cargo_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo nao encontrado.")
    user.cargo = cargo
    db.commit()
    return UsuarioCargoRead(
        id=user.id,
        nome=user.nome,
        email=user.email,
        perfil=user.perfil,
        cargo_id=cargo.id,
        cargo_nome=cargo.nome,
    )
