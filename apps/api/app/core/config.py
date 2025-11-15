from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from typing import Any
import json

from pydantic import Field, PostgresDsn, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parents[3] / ".env", extra="ignore")

    project_name: str = "Renderly API"
    api_prefix: str = "/api"
    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://renderly:renderly@db:5432/renderly"
    )
    access_token_expire_minutes: int = 60 * 24
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS"),
    )
    minio_endpoint: str = "storage:9000"
    minio_bucket: str = "renderly-pages"
    minio_access_key: str = "renderly"
    minio_secret_key: str = "renderlysecret"
    minio_secure: bool = False
    minio_presign_exp_seconds: int = 3600
    asset_bucket: str = "renderly-assets"
    asset_max_bytes: int = 10 * 1024 * 1024
    asset_presign_exp_seconds: int = 3600
    asset_thumbnail_size: int = 480
    asset_public_base: str | None = Field(
        default="http://localhost:8000/api",
        alias="ASSET_PUBLIC_BASE",
    )
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"
    domain_manager_url: str = "http://domain-manager:8080"
    custom_domain_cname_target: str = "pages.renderly.local"
    custom_domain_proxy_scheme: str = "https"
    custom_domain_local_dir: str | None = "/var/renderly/domains"
    project_subdomain_root: str | None = Field(default="pages.renderly.local", alias="PROJECT_SUBDOMAIN_ROOT")
    project_subdomain_scheme: str | None = Field(
        default=None,
        alias="PROJECT_SUBDOMAIN_SCHEME",
    )
    portal_url: str = Field(
        default="https://renderly.app/login",
        alias="PORTAL_URL",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, value: Any) -> list[str]:
        if value is None:
            return ["http://localhost:5173"]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [item.strip() for item in parsed if isinstance(item, str) and item.strip()]
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        raise ValueError("cors_origins must be a list or comma-separated string")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
