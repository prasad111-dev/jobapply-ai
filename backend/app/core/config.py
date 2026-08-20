import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "JobApply AI"
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "jobapply"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    OPENAI_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    RESUME_STORAGE_PATH: str = "uploads/resumes"
    MAX_FILE_SIZE_MB: int = 10
    BROWSER_TIMEOUT_SECONDS: int = 45
    CREDENTIALS_ENCRYPTED: bool = True
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_TLS: bool = True
    DIGEST_INTERVAL_HOURS: int = 24

    class Config:
        env_file = ".env"

    @property
    def resolved_secret_key(self) -> str:
        if self.SECRET_KEY:
            return self.SECRET_KEY
        if self.ENVIRONMENT.lower() in ("production", "prod"):
            raise RuntimeError(
                "SECRET_KEY is required in production. "
                "Set a strong value in backend/.env (e.g. `openssl rand -hex 32`). "
                "Refusing to start: a random per-process key would break token "
                "validation and credential decryption on every restart."
            )
        return secrets.token_urlsafe(48)


@lru_cache()
def get_settings() -> Settings:
    return Settings()