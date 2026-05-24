"""Application configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "credential-gateway"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "sqlite+aiosqlite:///credential_gateway.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"

    rate_limit_enabled: bool = True
    rate_limit_default: int = 100
    rate_limit_window_seconds: int = 60

    auth_timestamp_tolerance_seconds: int = 300
    auth_require_nonce: bool = True
    admin_token: str = "admin-secret-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
