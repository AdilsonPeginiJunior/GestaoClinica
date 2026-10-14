"""
Ponto de entrada da API do protótipo Gestão Clínica.

No startup: cria tabelas SQLite e executa seed de demonstração.
Documentação interativa: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import agendamentos, admin, auth, dashboard, financeiro, pacientes, prontuario, psicologos
from app.seed import seed_authorization, seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Cria estrutura e dados fictícios na primeira subida do servidor
    Base.metadata.create_all(bind=engine)
    if "cargo_id" not in {column["name"] for column in inspect(engine).get_columns("usuarios")}:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE usuarios ADD COLUMN cargo_id INTEGER REFERENCES cargos(id)"
            ))
    db = SessionLocal()
    try:
        seed_database(db)
        seed_authorization(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(pacientes.router)
app.include_router(psicologos.router)
app.include_router(agendamentos.router)
app.include_router(prontuario.router)
app.include_router(financeiro.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    """Verificacao rapida se a API esta respondendo (util para recepcao/dev)."""
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Gestao Clinica API", "docs": "/docs"}
