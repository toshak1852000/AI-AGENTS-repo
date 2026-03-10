"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-untyped]
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    postgres_db: str = "portfolioq"
    postgres_user: str = "portfolioq"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = ""
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = ""
    
    # Celery Configuration
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    
    # API Keys - Market Data Providers
    alpha_vantage_api_key: str = ""
    yahoo_finance_api_key: str = ""
    fred_api_key: str = ""
    
    # Application Settings
    secret_key: str = ""
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"
    
    # Backend API Configuration
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    
    # LangGraph Configuration
    langsmith_api_key: str = ""
    langsmith_project: str = "portfolioq"
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@portfolioq.com"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Build database URL if not provided (PostgreSQL only; project uses PostgreSQL end-to-end)
        if not self.database_url:
            self.database_url = (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        else:
            url = (self.database_url or "").strip()
            if url and not url.lower().startswith("postgresql"):
                raise ValueError(
                    "database_url must point to PostgreSQL; this project uses PostgreSQL end-to-end."
                )
        # Build Redis URL if not provided
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"
        # Set Celery URLs if not provided
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url


# Global settings instance
settings = Settings()
