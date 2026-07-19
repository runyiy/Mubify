from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


try:
    settings = Settings()
except ValidationError as exc:
    missing_fields = [
        str(error["loc"][0])
        for error in exc.errors()
        if error.get("type") == "missing" and error.get("loc")
    ]
    missing_text = ", ".join(missing_fields) or "required settings"

    raise RuntimeError(
        "Missing backend configuration: "
        f"{missing_text}. Create .env from .env.example "
        "or set these environment variables before starting the app. "
        f"Expected env file location: {ENV_FILE}"
    ) from exc
