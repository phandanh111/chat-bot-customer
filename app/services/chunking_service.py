"""
Document chunking service.
Uses RecursiveCharacterTextSplitter to split documents into
semantically meaningful chunks optimized for Vietnamese text.
"""

import hashlib
import logging
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks."""

    # Separators ordered by priority, optimized for Vietnamese documents:
    # 1. Double newline (paragraph boundary)
    # 2. Single newline (line break)
    # 3. Period + space (sentence boundary - Vietnamese)
    # 4. Exclamation/Question marks (sentence boundary)
    # 5. Semicolon (clause boundary)
    # 6. Comma + space (sub-clause)
    # 7. Space (word boundary)
    # 8. Empty string (character-level fallback)
    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    def __init__(self) -> None:
        settings = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.EXERCISE_EMBED_LIMIT,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=self.SEPARATORS,
            length_function=len,
            is_separator_regex=False,
        )

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def chunk_text(
        self,
        text: str,
        source: str = "unknown",
        extra_metadata: Optional[dict] = None,
    ) -> list[DocumentChunk]:
        """
        Split a text string into chunks.

        Args:
            text: The text content to chunk.
            source: Source identifier (e.g., filename).
            extra_metadata: Additional metadata to attach to each chunk.

        Returns:
            List of DocumentChunk objects.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking, skipping.")
            return []

        raw_chunks = self._splitter.split_text(text)
        chunks: list[DocumentChunk] = []

        for idx, chunk_content in enumerate(raw_chunks):
            metadata = {
                "source": source,
                "chunk_index": idx,
                "total_chunks": len(raw_chunks),
            }
            if extra_metadata:
                metadata.update(extra_metadata)

            chunk_id = self._generate_chunk_id(source, idx, chunk_content)

            chunks.append(
                DocumentChunk(
                    content=chunk_content,
                    metadata=metadata,
                    chunk_id=chunk_id,
                )
            )

        logger.info(
            "Chunked '%s' into %d chunks (chunk_size=%d, overlap=%d)",
            source,
            len(chunks),
            self._splitter._chunk_size,
            self._splitter._chunk_overlap,
        )
        return chunks

    # ──────────────────────────────────────────
    # Private Helpers
    # ──────────────────────────────────────────

    @staticmethod
    def _generate_chunk_id(source: str, index: int, content: str) -> str:
        """Generate a deterministic chunk ID based on source, index, and content hash."""
        hash_input = f"{source}:{index}:{content[:100]}"
        return hashlib.md5(hash_input.encode("utf-8")).hexdigest()
