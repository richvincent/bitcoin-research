"""Application settings, loaded from environment (12-factor friendly).

All settings carry dev-safe defaults so the service boots with zero config
against SQLite, with every external integration in stub mode.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FLOYDE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    env: Literal["development", "staging", "production"] = "development"
    secret_key: str = "dev-insecure-secret-change-me-0123456789abcdef"
    access_token_expire_minutes: int = 60 * 24 * 7  # one week
    jwt_algorithm: str = "HS256"

    # Database. Default: local SQLite file next to the working dir.
    database_url: str = "sqlite:///./floyde.db"

    # Stripe
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    # Amazon Product Advertising API
    amazon_access_key: str | None = None
    amazon_secret_key: str | None = None
    amazon_partner_tag: str = "floyde-20"
    amazon_region: str = "us-east-1"

    # Bookkeeping sync
    bookkeeping_provider: Literal["none", "frappe", "akaunting"] = "none"
    bookkeeping_base_url: str | None = None
    bookkeeping_api_key: str | None = None

    # Concierge (Ruby)
    concierge_webhook_url: str | None = None

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def amazon_enabled(self) -> bool:
        return bool(self.amazon_access_key and self.amazon_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
