"""
Vector store service.
Manages ChromaDB operations: storing and retrieving document embeddings.
"""

import logging

import chromadb

from app.config import get_settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for interacting with ChromaDB vector store."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self._collection = self._client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' ready (%d documents).",
            settings.COLLECTION_NAME,
            self._collection.count(),
        )

    # ──────────────────────────────────────────
    # Write Operations
    # ──────────────────────────────────────────

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """
        Add document chunks with their embeddings to the collection.

        Args:
            ids: Unique IDs for each document chunk.
            documents: Text content of each chunk.
            embeddings: Embedding vectors.
            metadatas: Metadata dicts for each chunk.
        """
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Upserted %d documents into ChromaDB.", len(ids))

    # ──────────────────────────────────────────
    # Read Operations
    # ──────────────────────────────────────────

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 4,
    ) -> dict:
        """
        Search for the most similar documents to the query embedding.

        Args:
            query_embedding: The embedding vector of the query.
            n_results: Number of results to return.

        Returns:
            ChromaDB query results dict with keys:
            ids, documents, metadatas, distances.
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        return results

    def get_collection_info(self) -> dict:
        """Get information about the current collection."""
        return {
            "collection_name": self._collection.name,
            "total_documents": self._collection.count(),
            "metadata": self._collection.metadata,
        }

    # ──────────────────────────────────────────
    # Management Operations
    # ──────────────────────────────────────────

    def clear_collection(self) -> None:
        """Delete all documents from the collection."""
        settings = get_settings()
        self._client.delete_collection(name=settings.COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("Collection '%s' cleared.", settings.COLLECTION_NAME)
