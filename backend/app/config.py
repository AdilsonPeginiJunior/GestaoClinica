from typing import Literal
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

CHAVE_DEMO = "change-me-in-production-use-env"
BANCO_DEMO = "sqlite:///./gestao_clinica.db"
EMAILS_DEMO = ("recepcao@demo.com", "psicologo@demo.com", "socia@demo.com", "admin@demo.com")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True, frozen=True)

    app_name: str = "Gestao Clinica API"
    app_env: Literal["demo", "production"] = "demo"
    demo_seed: bool | None = None
    database_url: str = Field(default=BANCO_DEMO, repr=False)
    secret_key: str = Field(default=CHAVE_DEMO, repr=False)
    algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=480, gt=0)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @property
    def demo_seed_ativo(self) -> bool:
        return self.app_env == "demo" and self.demo_seed is not False

    @model_validator(mode="after")
    def validar_producao(self):
        if self.app_env == "production":
            if self.demo_seed is True:
                raise ValueError("DEMO_SEED não pode ser habilitado em produção.")
            chave = self.secret_key
            exemplos = ("change-me", "change_me", "chave-longa", "your-secret", "replace", "troque", "exemplo")
            if (len(chave) < 32 or len(set(chave)) < 8 or chave != chave.strip()
                    or chave == CHAVE_DEMO or any(t in chave.lower() for t in exemplos)):
                raise ValueError("Produção exige SECRET_KEY aleatória, com pelo menos 32 caracteres, sem valor padrão ou de exemplo.")
            if "database_url" not in self.model_fields_set or not self.database_url.strip() or self.database_url == BANCO_DEMO:
                raise ValueError("Produção exige DATABASE_URL explícita, diferente do banco padrão de demonstração.")
            try:
                url = make_url(self.database_url)
            except ArgumentError:
                raise ValueError("DATABASE_URL inválida para produção.") from None
            if (url.get_backend_name() == "sqlite" and url.database not in (None, ":memory:")
                    and Path(url.database).resolve() == Path("gestao_clinica.db").resolve()):
                raise ValueError("Use uma base separada do arquivo padrão de demonstração.")
            if "*" in self.cors_origins:
                raise ValueError("Produção exige origens CORS explícitas, sem curinga.")
        return self


settings = Settings()
