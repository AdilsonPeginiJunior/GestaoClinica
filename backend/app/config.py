from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Gestao Clinica API"
    database_url: str = "sqlite:///./gestao_clinica.db"
    secret_key: str = "change-me-in-production-use-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


settings = Settings()
