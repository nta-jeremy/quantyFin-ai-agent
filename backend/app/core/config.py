from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, model_validator
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

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

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
