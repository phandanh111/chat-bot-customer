import logging

from sentence_transformers import CrossEncoder

from app.config import get_settings

logger = logging.getLogger(__name__)

_reranker_instance: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    global _reranker_instance
    if _reranker_instance is None:
        settings = get_settings()
        logger.info("Loading reranker model: %s ...", settings.RERANKER_MODEL)
        _reranker_instance = CrossEncoder(settings.RERANKER_MODEL)
        logger.info("Reranker model loaded successfully.")
    return _reranker_instance


class RerankingService:
    def __init__(self) -> None:
        self._model = _get_reranker()

    def rerank(self, query: str, documents: list[str], top_k: int) -> list[tuple[int, float]]:
        if not documents:
            return []
        pairs = [(query, doc) for doc in documents]
        scores: list[float] = self._model.predict(pairs).tolist()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
