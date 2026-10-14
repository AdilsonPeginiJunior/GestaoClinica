"""
Autenticacao JWT e controle de acesso por perfil (RBAC).

Perfis: recepcionista, psicologo, socia, admin — ver require_perfis() nos routers.
Senhas: bcrypt direto (evita incompatibilidade passlib + bcrypt 4.2+).
"""

from datetime import datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import PerfilUsuario, Usuario
from app.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Conjuntos reutilizados nos routers para checagem de permissao
PERFIS_GESTAO = {PerfilUsuario.admin, PerfilUsuario.socia, PerfilUsuario.recepcionista}
PERFIS_FINANCEIRO = {PerfilUsuario.admin, PerfilUsuario.socia}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara senha em texto puro com hash armazenado no banco."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Gera hash bcrypt para cadastro/seed de usuarios."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Emite JWT com expiracao configuravel (settings.access_token_expire_minutes)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def authenticate_user(db: Session, email: str, password: str) -> Usuario | None:
    """Retorna usuario se e-mail/senha validos e conta ativa."""
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not user.ativo:
        return None
    if not verify_password(password, user.senha_hash):
        return None
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    """Dependency: extrai usuario do Bearer token em rotas protegidas."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(sub=email)
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(Usuario).filter(Usuario.email == token_data.sub).first()
    if user is None or not user.ativo:
        raise credentials_exception
    return user


def require_perfis(*perfis: PerfilUsuario):
    """Factory de dependency: restringe rota aos perfis informados."""

    allowed = set(perfis)

    def _checker(current_user: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
        if current_user.perfil not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
        return current_user

    return _checker


def has_permission(user: Usuario, permission_key: str) -> bool:
    """Consulta as permissões explícitas do cargo, sem conceder acesso implícito."""
    return bool(
        user.cargo
        and any(permission.chave == permission_key for permission in user.cargo.permissoes)
    )


def require_permission(*permission_keys: str):
    """Permite a rota se o cargo possuir ao menos uma das permissões informadas."""

    def _checker(current_user: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
        if not any(has_permission(current_user, key) for key in permission_keys):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
        return current_user

    return _checker
