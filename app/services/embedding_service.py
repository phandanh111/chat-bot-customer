"""
Embedding service.
Uses sentence-transformers to generate embeddings with the
dangvantuan/vietnamese-embedding model.
"""

import logging
from typing import Union

from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton to avoid reloading the model
_model_instance: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load and cache the embedding model."""
    global _model_instance
    if _model_instance is None:
        settings = get_settings()
        logger.info("Loading embedding model: %s ...", settings.EMBED_MODEL)
        _model_instance = SentenceTransformer(settings.EMBED_MODEL)
        logger.info("Embedding model loaded successfully.")
    return _model_instance


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self) -> None:
        self._model = _get_model()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).
        """
        if not texts:
            return []

        logger.debug("Embedding %d texts...", len(texts))
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a single query string.

        Args:
            query: The query text.

        Returns:
            Embedding vector as a list of floats.
        """
        embeddings = self._model.encode(
            [query],
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings[0].tolist()

    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self._model.get_sentence_embedding_dimension()
