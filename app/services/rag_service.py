import logging
import re
from collections.abc import AsyncIterator
from pathlib import Path

from app.config import get_settings
from app.constants import (
    ACRONYM_NORMALIZATIONS,
    LOCATION_KEYWORD_PATTERNS,
    MARKDOWN_EXTENSIONS,
    NO_CONTEXT_REPLY,
    RETRIEVAL_QUERY_MAX_CHARS,
    SUPPORTED_DOCUMENT_EXTENSIONS,
)
from app.models.schemas import (
    ChatResponse,
    DocumentChunk,
    IngestResponse,
    SourceDocument,
)
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.map_service import MapService
from app.services.markdown_chunking_service import MarkdownChunkingService
from app.services.vector_store import VectorStoreService
from app.utils.document_loader import load_document

logger = logging.getLogger(__name__)

_ACRONYM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE), v)
    for k, v in ACRONYM_NORMALIZATIONS.items()
]


class RAGService:
    def __init__(self) -> None:
        self._chunking = ChunkingService()
        self._markdown_chunking = MarkdownChunkingService()
        self._embedding = EmbeddingService()
        self._vector_store = VectorStoreService()
        self._llm = LLMService()
        self._map_service = MapService()
        self._settings = get_settings()

    def ingest_file(self, file_path: str | Path) -> int:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = load_document(file_path)
        if not text.strip():
            logger.warning("File '%s' is empty, skipping.", file_path.name)
            return 0

        chunker = self._select_chunker(file_path)
        chunks = chunker.chunk_text(text=text, source=file_path.name)
        if not chunks:
            return 0

        chunk_texts = [c.content for c in chunks]
        embeddings = self._embedding.embed_texts(chunk_texts)
        self._vector_store.add_documents(
            ids=[c.chunk_id for c in chunks],
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=[c.metadata for c in chunks],
        )
        logger.info("Ingested '%s': %d chunks stored.", file_path.name, len(chunks))
        return len(chunks)

    def _select_chunker(self, file_path: Path):
        if file_path.suffix.lower() in MARKDOWN_EXTENSIONS:
            logger.info("Using MARKDOWN HEADER chunking for '%s'", file_path.name)
            return self._markdown_chunking
        logger.info("Using RECURSIVE TEXT chunking for '%s'", file_path.name)
        return self._chunking

    def ingest_directory(self, dir_path: str | Path) -> IngestResponse:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        total_chunks = 0
        processed_files: list[str] = []
        for file_path in sorted(dir_path.iterdir()):
            if file_path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS:
                try:
                    total_chunks += self.ingest_file(file_path)
                    processed_files.append(file_path.name)
                except Exception as exc:
                    logger.error("Failed to ingest '%s': %s", file_path.name, exc)

        return IngestResponse(
            message=f"Ingested {len(processed_files)} files with {total_chunks} chunks.",
            total_chunks=total_chunks,
            files_processed=processed_files,
        )

    @staticmethod
    def _normalize_query(query: str) -> str:
        for pattern, replacement in _ACRONYM_PATTERNS:
            query = pattern.sub(replacement, query)
        return query

    @staticmethod
    def _build_retrieval_query(question: str) -> str:
        return question.strip()[:RETRIEVAL_QUERY_MAX_CHARS]

    @staticmethod
    def _detect_location(question: str) -> str | None:
        q = question.lower()
        for pattern in LOCATION_KEYWORD_PATTERNS:
            m = pattern.search(q)
            if m:
                return m.group(0)
        return None

    async def query(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> ChatResponse:
        context, sources = await self._build_context(question)
        if not context.strip():
            return ChatResponse(answer=NO_CONTEXT_REPLY, sources=sources)

        answer = await self._llm.generate(question=question, context=context)
        return ChatResponse(answer=answer, sources=sources)

    async def stream_query(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[AsyncIterator[str], list[SourceDocument]]:
        context, sources = await self._build_context(question)
        if not context.strip():
            async def _fallback() -> AsyncIterator[str]:
                yield NO_CONTEXT_REPLY

            return _fallback(), sources

        return self._llm.generate_stream(question=question, context=context), sources

    async def _build_context(self, question: str) -> tuple[str, list[SourceDocument]]:
        normalized = self._normalize_query(question)
        retrieval_query = self._build_retrieval_query(normalized)
        query_embedding = self._embedding.embed_query(retrieval_query)

        results = self._vector_store.search(
            query_embedding=query_embedding,
            n_results=self._settings.EXERCISE_CONTEXT_LIMIT,
        )

        context_parts: list[str] = []
        sources: list[SourceDocument] = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                context_parts.append(doc)
                sources.append(
                    SourceDocument(
                        content=doc,
                        source=meta.get("source", "unknown"),
                        chunk_index=meta.get("chunk_index", 0),
                        score=round(1 - dist, 4),
                    )
                )

        context = "\n\n".join(context_parts)

        location = self._detect_location(question)
        if location:
            map_injection = await self._map_service.get_closest_branches(location)
            if map_injection:
                context = map_injection + "\n\n" + context

        return context, sources
