"""
Configuration settings for QuantyFinAI Agent.

This module provides centralized configuration management using Pydantic settings.
"""

import os
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    url: str = Field(default="postgresql://quantyfin:quantyfin123@localhost:5432/quantyfin")
    pool_size: int = Field(default=20, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=1)
    echo: bool = Field(default=False)


class RedisSettings(BaseModel):
    """Redis configuration settings."""

    url: str = Field(default="redis://localhost:6379")
    max_connections: int = Field(default=10, ge=1)
    retry_on_timeout: bool = Field(default=True)
    socket_timeout: int = Field(default=5, ge=1)
    socket_connect_timeout: int = Field(default=5, ge=1)


class KeycloakSettings(BaseModel):
    """Keycloak authentication configuration settings."""

    server_url: str = Field(default="http://localhost:8080")
    realm: str = Field(default="quantyfin")
    client_id: str = Field(default="quantyfin-api")
    client_secret: SecretStr = Field(default=SecretStr("default-secret"))
    algorithm: str = Field(default="RS256")


class LLMProviderSettings(BaseModel):
    """LLM provider configuration settings."""

    openai_api_key: Optional[SecretStr] = Field(default=None)
    anthropic_api_key: Optional[SecretStr] = Field(default=None)
    google_api_key: Optional[SecretStr] = Field(default=None)
    deepseek_api_key: Optional[SecretStr] = Field(default=None)


class OpenAISettings(BaseModel):
    """OpenAI-specific configuration settings."""

    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1)
    embedding_model: str = Field(default="text-embedding-ada-002")
    vector_dimension: int = Field(default=1536, ge=1)


class ExternalAPISettings(BaseModel):
    """External API configuration settings."""

    news_api_key: Optional[SecretStr] = Field(default=None)
    alpha_vantage_api_key: Optional[SecretStr] = Field(default=None)
    vnstock_api_key: Optional[SecretStr] = Field(default=None)

    timeout: int = Field(default=30, ge=1)
    retry_attempts: int = Field(default=3, ge=1)


class LoggingSettings(BaseModel):
    """Logging configuration settings."""

    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file_path: Optional[str] = Field(default=None)
    max_file_size: str = Field(default="10MB")
    backup_count: int = Field(default=5, ge=0)


class SecuritySettings(BaseModel):
    """Security configuration settings."""

    secret_key: SecretStr = Field(default=SecretStr("your-secret-key-here"))
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)
    allowed_hosts: List[str] = Field(default=["*"])


class AppSettings(BaseModel):
    """Application configuration settings."""

    name: str = Field(default="QuantyFinAI Agent")
    version: str = Field(default="0.1.0")
    description: str = Field(default="AI-powered financial analysis and stock prediction system")
    debug: bool = Field(default=True)
    environment: str = Field(default="development")
    api_v1_prefix: str = Field(default="/api/v1")

    # CORS settings
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])


class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="allow",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    keycloak: KeycloakSettings = Field(default_factory=KeycloakSettings)
    llm: LLMProviderSettings = Field(default_factory=LLMProviderSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    external_apis: ExternalAPISettings = Field(default_factory=ExternalAPISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    # Additional fields from .env.example
    environment: str = Field(default="development")
    secret_key: SecretStr = Field(default=SecretStr("your-secret-key-here"))
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment.lower() in ["development", "dev"]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment.lower() in ["production", "prod"]

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app.environment.lower() in ["testing", "test"]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings