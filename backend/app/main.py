"""
Ponto de entrada da API do protótipo Gestão Clínica.

No startup: cria tabelas SQLite e executa seed de demonstração.
Documentação interativa: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import agendamentos, auth, dashboard, financeiro, pacientes, psicologos
from app.seed import seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Cria estrutura e dados fictícios na primeira subida do servidor
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
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
app.include_router(pacientes.router)
app.include_router(psicologos.router)
app.include_router(agendamentos.router)
app.include_router(financeiro.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    """Verificacao rapida se a API esta respondendo (util para recepcao/dev)."""
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Gestao Clinica API", "docs": "/docs"}
