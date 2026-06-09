import logging

import chromadb

from app.config import get_settings
from app.constants import VECTOR_STORE_DISTANCE_METRIC

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self._collection = self._client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": VECTOR_STORE_DISTANCE_METRIC},
        )
        logger.info(
            "ChromaDB collection '%s' ready (%d documents).",
            settings.COLLECTION_NAME,
            self._collection.count(),
        )

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self._collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        logger.info("Upserted %d documents into ChromaDB.", len(ids))

    def search(self, query_embedding: list[float], n_results: int = 4) -> dict:
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    def get_collection_info(self) -> dict:
        return {
            "collection_name": self._collection.name,
            "total_documents": self._collection.count(),
            "metadata": self._collection.metadata,
        }

    def delete_by_source(self, source: str) -> int:
        results = self._collection.get(where={"source": source}, include=[])
        if not results["ids"]:
            return 0
        self._collection.delete(ids=results["ids"])
        logger.info("Deleted %d chunks for source '%s'.", len(results["ids"]), source)
        return len(results["ids"])

    def clear_collection(self) -> None:
        settings = get_settings()
        self._client.delete_collection(name=settings.COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": VECTOR_STORE_DISTANCE_METRIC},
        )
        logger.warning("Collection '%s' cleared.", settings.COLLECTION_NAME)
