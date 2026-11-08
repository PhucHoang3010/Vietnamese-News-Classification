"""Cấu hình ứng dụng, đọc từ biến môi trường hoặc file .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    app_name: str = "TalentLens – Kho dữ liệu tuyển dụng AI"
    environment: str = "development"

    # PostgreSQL (Render/Neon cung cấp dạng postgres://... -> tự chuẩn hoá)
    database_url: str = "postgresql+psycopg://hr_admin:hr_admin_pw@localhost:5432/recruitment_dw"

    # Xác thực
    jwt_secret: str = "dev-secret-change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480

    # AI: "auto" = dùng Claude nếu có API key, ngược lại dùng engine NLP nội bộ
    ai_provider: str = "auto"  # auto | claude | local
    anthropic_api_key: str | None = None
    llm_model: str = "claude-opus-5-5"
    llm_effort: str = "medium"
    llm_timeout_seconds: float = 90.0

    # Dữ liệu
    sample_data_dir: Path = BASE_DIR / "data" / "raw"
    upload_dir: Path = BASE_DIR / "data" / "uploads"
    seed_demo: bool = True

    # Mật khẩu mặc định cho tài khoản demo (nên đổi khi deploy thật)
    admin_password: str = "Admin@123"
    demo_password: str = "Demo@123"

    cors_origins: str = "*"

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            value = "postgresql+psycopg://" + value[len("postgres://"):]
        elif value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value[len("postgresql://"):]
        return value

    @property
    def use_claude(self) -> bool:
        if self.ai_provider == "local":
            return False
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
