"""Bootstrap explícito: python -m app.criar_admin --email administrador@clinica.com."""
import argparse
from getpass import getpass

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import update

from app.auth import get_password_hash
from app.config import EMAILS_DEMO, settings
from app.database import SessionLocal
from app.models import Cargo, PerfilUsuario, Usuario
from app.seed import verificar_banco_producao
from app.transacoes import transacao


def criar_primeiro_admin(db, email: str, nome: str, senha: str):
    if settings.app_env != "production":
        raise ValueError("Este comando é exclusivo do modo production.")
    email = str(TypeAdapter(EmailStr).validate_python(email))
    if email.lower() in EMAILS_DEMO:
        raise ValueError("Use um endereço próprio, diferente das contas de demonstração.")
    if not nome.strip() or len(nome.strip()) > 120 or len(senha) < 12 or len(senha.encode("utf8")) > 72:
        raise ValueError("Informe nome de até 120 caracteres e senha de pelo menos 12 caracteres (até 72 bytes UTF-8).")
    with transacao(db):
        verificar_banco_producao(db)
        cargo = db.query(Cargo).filter_by(nome="Administrador").first()
        if cargo is None:
            raise ValueError("Inicie a API de produção primeiro para preparar o catálogo de cargos.")
        db.execute(update(Cargo).where(Cargo.id == cargo.id).values(id=Cargo.id)
                   .execution_options(synchronize_session=False))
        if db.query(Usuario.id).filter(Usuario.perfil == PerfilUsuario.admin).first():
            raise ValueError("Já existe administrador. O comando não cria outro nem redefine senhas.")
        db.add(Usuario(nome=nome.strip(), email=email, senha_hash=get_password_hash(senha),
                       perfil=PerfilUsuario.admin, cargo_id=cargo.id, ativo=True))


def main():
    parser = argparse.ArgumentParser(description="Cria somente o primeiro administrador da base de produção.")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    if settings.app_env != "production":
        parser.error("Configure APP_ENV=production e uma base separada antes de executar.")
    nome = input("Nome do administrador: ")
    senha = getpass("Senha (mínimo 12 caracteres): ")
    if senha != getpass("Confirme a senha: "):
        parser.error("As senhas não conferem.")
    try:
        with SessionLocal() as db:
            criar_primeiro_admin(db, args.email, nome, senha)
    except Exception:
        parser.exit(1, "Não foi possível criar o administrador. Confira configuração, schema, dados informados e existência de administrador. Nenhuma senha é exibida.\n")
    print("Primeiro administrador criado. Nenhum dado de demonstração foi incluído.")


if __name__ == "__main__":
    main()
