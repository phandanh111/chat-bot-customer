import asyncio
import hashlib
import logging
import re
from collections.abc import AsyncIterator
from pathlib import Path

from cachetools import TTLCache

from app.config import get_settings
from app.constants import (
    ACRONYM_NORMALIZATIONS,
    LOCATION_KEYWORD_PATTERNS,
    MARKDOWN_EXTENSIONS,
    MIN_RELEVANCE_SCORE,
    NO_CONTEXT_REPLY,
    RETRIEVAL_MAX_CHUNKS_PER_SOURCE,
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
from app.services.query_rewriter_service import QueryRewriterService
from app.services.vector_store import VectorStoreService
from app.utils.document_loader import load_document

logger = logging.getLogger(__name__)

_ACRONYM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE), v)
    for k, v in ACRONYM_NORMALIZATIONS.items()
]


_CONTEXT_CACHE: TTLCache = TTLCache(maxsize=256, ttl=3600)


class RAGService:
    def __init__(self) -> None:
        self._chunking = ChunkingService()
        self._markdown_chunking = MarkdownChunkingService()
        self._embedding = EmbeddingService()
        self._vector_store = VectorStoreService()
        self._llm = LLMService()
        self._map_service = MapService()
        self._query_rewriter = QueryRewriterService()
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
        context, sources = await self._build_context(question, history)
        if not context.strip():
            return ChatResponse(answer=NO_CONTEXT_REPLY, sources=sources)

        answer = await self._llm.generate(question=question, context=context, history=history)
        return ChatResponse(answer=answer, sources=sources)

    async def stream_query(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[AsyncIterator[str], list[SourceDocument]]:
        context, sources = await self._build_context(question, history)
        if not context.strip():
            async def _fallback() -> AsyncIterator[str]:
                yield NO_CONTEXT_REPLY

            return _fallback(), sources

        return self._llm.generate_stream(question=question, context=context, history=history), sources

    async def _build_context(self, question: str, history: list[dict[str, str]] | None = None) -> tuple[str, list[SourceDocument]]:
        normalized = self._normalize_query(question)
        retrieval_query = self._build_retrieval_query(normalized)
        retrieval_query = await self._query_rewriter.rewrite(retrieval_query, history=history)

        cache_key = hashlib.md5(retrieval_query.encode()).hexdigest()
        if cache_key in _CONTEXT_CACHE:
            logger.debug("Context cache hit for query: %s...", retrieval_query[:60])
            cached_context, cached_sources = _CONTEXT_CACHE[cache_key]
        else:
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(None, self._embedding.embed_query, retrieval_query)

            results = await loop.run_in_executor(
                None,
                lambda: self._vector_store.search(
                    query_embedding=query_embedding,
                    n_results=self._settings.EXERCISE_CONTEXT_LIMIT,
                ),
            )

            candidate_docs: list[str] = []
            candidate_metas: list[dict] = []
            candidate_scores: list[float] = []
            if results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    score = round(1 - dist, 4)
                    if score < MIN_RELEVANCE_SCORE:
                        logger.debug("Skipping chunk (score=%.4f < threshold=%.2f): %s...", score, MIN_RELEVANCE_SCORE, doc[:60])
                        continue
                    candidate_docs.append(doc)
                    candidate_metas.append(meta)
                    candidate_scores.append(score)

            # Rank by cosine score (descending), enforce per-source diversity
            sorted_indices = sorted(
                range(len(candidate_scores)),
                key=lambda i: candidate_scores[i],
                reverse=True,
            )

            context_parts: list[str] = []
            cached_sources: list[SourceDocument] = []
            source_counts: dict[str, int] = {}
            for i in sorted_indices:
                if len(context_parts) >= self._settings.RERANKER_TOP_K:
                    break
                doc = candidate_docs[i]
                meta = candidate_metas[i]
                src = meta.get("source", "unknown")
                if source_counts.get(src, 0) >= RETRIEVAL_MAX_CHUNKS_PER_SOURCE:
                    continue
                source_counts[src] = source_counts.get(src, 0) + 1
                context_parts.append(doc)
                cached_sources.append(
                    SourceDocument(
                        content=doc,
                        source=meta.get("source", "unknown"),
                        chunk_index=meta.get("chunk_index", 0),
                        score=round(candidate_scores[i], 4),
                    )
                )

            cached_context = "\n\n".join(context_parts)
            _CONTEXT_CACHE[cache_key] = (cached_context, cached_sources)

        context = cached_context
        sources = list(cached_sources)

        location = self._detect_location(question)
        if location:
            map_injection = await self._map_service.get_closest_branches(location)
            if map_injection:
                context = map_injection + "\n\n" + context

        return context, sources
