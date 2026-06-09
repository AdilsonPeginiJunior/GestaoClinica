"""
Conexao com SQLite (protótipo) ou PostgreSQL (producao).

WAL + timeout reduzem travamentos quando ha varias requisicoes simultaneas.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(settings.database_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _sqlite_pragma(dbapi_connection, connection_record):
    """Melhora concorrencia do SQLite em ambiente web."""
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
