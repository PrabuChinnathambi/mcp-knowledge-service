from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "mcp-knowledge-service"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # Database & Storage
    DATABASE_URL: str = "postgresql+asyncpg://knowledge:knowledge_password@localhost:5432/knowledge_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin_secret"
    MINIO_BUCKET: str = "knowledge-docs"
    MINIO_SECURE: bool = False

    # Embedding & LLM
    EMBEDDING_PROVIDER: Literal["ollama", "local", "openai", "mock"] = "ollama"
    EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    EMBEDDING_DIMENSIONS: int = 768
    OLLAMA_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:7b-instruct"

    # Ingestion Parameters
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    MIN_RELEVANCE: float = 0.30

    # Security & RBAC
    API_KEY: str = "dev-secret-key"
    MCP_USER_ID: str = "alice"
    ALLOWED_TOOLS: str = "list_collections,search_knowledge,ask_docs,ingest_document"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
