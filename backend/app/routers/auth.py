"""Login JWT e dados do usuario autenticado."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.config import settings
from app.database import get_db
from app.models import Usuario
from app.schemas import LoginRequest, Token, UsuarioMe

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha invalidos")
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=token)


@router.get("/me", response_model=UsuarioMe)
def me(current_user: Usuario = Depends(get_current_user)):
    psicologo_nome = current_user.psicologo.nome if current_user.psicologo else None
    return UsuarioMe(
        id=current_user.id,
        nome=current_user.nome,
        email=current_user.email,
        perfil=current_user.perfil,
        ativo=current_user.ativo,
        psicologo_id=current_user.psicologo_id,
        psicologo_nome=psicologo_nome,
    )
