"""
Ponto de entrada da API do protótipo Gestão Clínica.

No startup: prepara o schema e só cria dados fictícios quando o modo demo permite.
Documentação interativa: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import agendamentos, admin, auth, dashboard, financeiro, pacientes, prontuario, psicologos, recorrencias
from app.seed import seed_authorization, seed_database, verificar_banco_producao
from app.schema_financeiro import atualizar_schema_financeiro


@asynccontextmanager
async def lifespan(_: FastAPI):
    # A configuração já foi validada antes de criar a engine/importar a aplicação.
    Base.metadata.create_all(bind=engine)
    atualizar_schema_financeiro(engine)
    if "cargo_id" not in {column["name"] for column in inspect(engine).get_columns("usuarios")}:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE usuarios ADD COLUMN cargo_id INTEGER REFERENCES cargos(id)"
            ))
    db = SessionLocal()
    try:
        if settings.app_env == "production":
            verificar_banco_producao(db)
        if settings.demo_seed_ativo:
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
app.include_router(recorrencias.router)
app.include_router(prontuario.router)
app.include_router(financeiro.router)
app.include_router(dashboard.router)


@app.get("/api/config/publico")
def configuracao_publica():
    """Somente dados de apresentação; nunca expõe chave, banco ou credenciais."""
    return {"ambiente": settings.app_env, "demo_habilitada": settings.demo_seed_ativo}


@app.get("/health")
def health():
    """Verificacao rapida se a API esta respondendo (util para recepcao/dev)."""
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Gestao Clinica API", "docs": "/docs"}
