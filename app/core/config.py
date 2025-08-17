from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "MVP Project"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/users/v1"

    # Required
    DATABASE_URL: str  # must be provided via env/.env
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Optional flags
    FEATURE_LLM: bool = False
    LOG_LEVEL: str = "INFO"

    # JWT
    SECRET_KEY: str = "change-me"  # set in .env for prod
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            if "," in s:
                return [i.strip() for i in s.split(",") if i.strip()]
            return [s] if s else []
        return v


settings = Settings()
