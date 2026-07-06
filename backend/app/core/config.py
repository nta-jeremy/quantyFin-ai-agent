from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field, model_validator
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "quantyFin-ai"
    
    # PostgreSQL settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "quantyfin"
    
    # Neo4j settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LiteLLM/LLM settings
    LITELLM_API_KEY: str | None = None
    LITELLM_API_BASE: str | None = None
    LITELLM_MODEL: str = "gemini/gemini-1.5-flash"

    # Telegram settings
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # News crawler settings (news-crawler-fulltext)
    FETCH_CONCURRENCY_LIMIT: int = Field(default=4, ge=1, le=10)
    DEFAULT_TOP_N: int = Field(default=20, ge=1, le=100)
    MIN_CONTENT_LENGTH: int = Field(default=500, ge=1)
    FETCH_TIMEOUT: int = Field(default=30, ge=5, le=120)
    PER_SITE_RATE_LIMIT: float = Field(default=1.0, ge=0.1, le=10)
    CRAWLER_USER_AGENT: str = (
        "Mozilla/5.0 (compatible; quantyFin-ai-news-crawler/1.0; "
        "+https://github.com/quantyfin)"
    )

    @model_validator(mode='after')
    def validate_secrets(self) -> 'Settings':
        missing = []
        if not self.POSTGRES_PASSWORD:
            missing.append("POSTGRES_PASSWORD")
        if not self.NEO4J_PASSWORD:
            missing.append("NEO4J_PASSWORD")
        if not self.SECRET_KEY:
            missing.append("SECRET_KEY")
        if missing:
            raise ValueError(f"Required secrets not set: {', '.join(missing)}. Set them via environment variables or .env file.")
        return self
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        import urllib.parse
        password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

try:
    settings = Settings()
except Exception as e:
    import sys
    is_testing = "pytest" in sys.modules or os.getenv("TESTING") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
    if is_testing:
        settings = Settings(
            POSTGRES_PASSWORD="dummy_postgres_password",
            NEO4J_PASSWORD="dummy_neo4j_password",
            SECRET_KEY="dummy_secret_key"
        )
    else:
        raise e
