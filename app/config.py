"""
Application configuration management.
Loads settings from .env file using pydantic-settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "ministral-3:8b"

    # RAG Configuration
    EMBED_MODEL: str = "dangvantuan/vietnamese-embedding"
    EXERCISE_EMBED_LIMIT: int = 500
    EXERCISE_CONTEXT_LIMIT: int = 4

    # ChromaDB Configuration
    CHROMA_DB_PATH: str = "data/chroma_db"
    COLLECTION_NAME: str = "customer_support_docs"

    # Chunking Configuration
    CHUNK_OVERLAP: int = 50


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton)."""
    return Settings()
