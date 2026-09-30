"""
Pratighat.ai — App Config
Central configuration from environment / .env file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application identity
    # ------------------------------------------------------------------
    app_name: str = "Pratighat.ai"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development | staging | production

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_log_level: str = "info"
    server_workers: int = 1

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    secret_key: str = "change-this-to-a-random-512-bit-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    password_min_length: int = 12

    # CORS
    cors_allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://pratighat:pratighat@localhost:5432/pratighat"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # SQLite fallback for development (no PostgreSQL available)
    database_sqlite_url: str = "sqlite+aiosqlite:///./pratighat.db"

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300

    # ------------------------------------------------------------------
    # Celery / Task queue
    # ------------------------------------------------------------------
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_default_queue: str = "pratighat"
    engine_default_scan_timeout: int = 1800  # 30 minutes

    # ------------------------------------------------------------------
    # Engine paths
    # ------------------------------------------------------------------
    assets_storage_path: str = "/tmp/pratighat_assets"
    reports_storage_path: str = "/tmp/pratighat_reports"
    evidence_storage_path: str = "/tmp/pratighat_evidence"
    result_storage_path: str = "/tmp/pratighat_results"

    # ------------------------------------------------------------------
    # AI / LLM
    # ------------------------------------------------------------------
    llm_provider: str = "ollama"  # ollama | openai | anthropic | none
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3"
    llm_api_key: str = ""

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------
    feature_assessment_execution: bool = True
    feature_ai_analyst: bool = True
    feature_websocket_realtime: bool = True
    feature_report_export: bool = True
    feature_audit_integrity: bool = True

    # ------------------------------------------------------------------
    # Derived
    # ------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"

    def use_sqlite(self) -> bool:
        """Use SQLite when no PostgreSQL is available (dev/test)."""
        return self.is_development or self.is_test


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — reads .env once per process."""
    return Settings()


settings = get_settings()
