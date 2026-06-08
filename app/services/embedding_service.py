import logging
from typing import Union

from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)

_model_instance: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model_instance
    if _model_instance is None:
        settings = get_settings()
        logger.info("Loading embedding model: %s ...", settings.EMBED_MODEL)
        _model_instance = SentenceTransformer(settings.EMBED_MODEL)
        logger.info("Embedding model loaded successfully.")
    return _model_instance


class EmbeddingService:
    def __init__(self) -> None:
        self._model = _get_model()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True).tolist()

    def embed_query(self, query: str) -> list[float]:
        return self._model.encode(query, show_progress_bar=False, normalize_embeddings=True).tolist()

    @property
    def embedding_dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()
