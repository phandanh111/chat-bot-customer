import hashlib
import logging
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.constants import CHUNK_SEPARATORS
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)


class ChunkingService:
    def __init__(self) -> None:
        settings = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=CHUNK_SEPARATORS,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self, text: str, source: str = "unknown", extra_metadata: Optional[dict] = None) -> list[DocumentChunk]:
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking, skipping.")
            return []

        raw_chunks = self._splitter.split_text(text)
        chunks: list[DocumentChunk] = []
        for idx, chunk_content in enumerate(raw_chunks):
            metadata = {"source": source, "chunk_index": idx, "total_chunks": len(raw_chunks)}
            if extra_metadata:
                metadata.update(extra_metadata)
            chunks.append(DocumentChunk(
                content=chunk_content,
                metadata=metadata,
                chunk_id=self._generate_chunk_id(source, idx, chunk_content),
            ))

        logger.info(
            "Chunked '%s' into %d chunks (chunk_size=%d, overlap=%d)",
            source, len(chunks), self._splitter._chunk_size, self._splitter._chunk_overlap,
        )
        return chunks

    @staticmethod
    def _generate_chunk_id(source: str, index: int, content: str) -> str:
        return hashlib.md5(f"{source}:{index}:{content[:100]}".encode("utf-8")).hexdigest()
