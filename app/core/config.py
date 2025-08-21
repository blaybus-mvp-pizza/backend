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
    # SQLAlchemy
    SQL_ECHO: bool = False

    # JWT
    SECRET_KEY: str = "change-me"  # set in .env for prod
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # coolsms
    SENDER_NUMBER: str = ""
    SMS_API_KEY: str = ""
    SMS_API_SECRET: str = ""

    # AWS / S3
    AWS_REGION: str = "ap-northeast-2"
    AWS_S3_BUCKET_PRODUCTS: str = "nafalmvp-products"
    AWS_S3_BUCKET_STORES: str = "nafalmvp-popup-stores"
    AWS_S3_BUCKET_STORIES: str = "nafalmvp-stories"
    AWS_S3_BUCKET_USERS: str = "nafalmvp-users"

    # Upload constraints
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_MIME: str = "image/jpeg,image/png,image/webp"

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
