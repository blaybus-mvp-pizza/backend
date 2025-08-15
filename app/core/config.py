from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
	PROJECT_NAME: str = "MVP Project"
	VERSION: str = "0.1.0"
	API_V1_STR: str = "/api/v1"

	DATABASE_URL: str = "mysql+pymysql://mvp_user:mvp_password@localhost:3306/mvp_db"
	CORS_ORIGINS: List[str] = ["http://localhost:3000"]

	model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, case_sensitive=True)

	@field_validator("CORS_ORIGINS", mode="before")
	@classmethod
	def parse_cors_origins(cls, v):
		if isinstance(v, str):
			return [i.strip() for i in v.split(",") if i.strip()]
		return v


settings = Settings()
