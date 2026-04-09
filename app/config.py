from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "ministral-3:8b"

    EMBED_MODEL: str = "dangvantuan/vietnamese-embedding"
    EXERCISE_EMBED_LIMIT: int = 500
    EXERCISE_CONTEXT_LIMIT: int = 4

    CHROMA_DB_PATH: str = "data/chroma_db"
    COLLECTION_NAME: str = "customer_support_docs"

    CHUNK_OVERLAP: int = 50


@lru_cache()
def get_settings() -> Settings:
    return Settings()
