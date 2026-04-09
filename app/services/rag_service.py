"""
RAG service.
Orchestrates the full RAG pipeline: ingest documents and answer queries.
"""

import logging
from pathlib import Path

from app.config import get_settings
from app.models.schemas import (
    ChatResponse,
    DocumentChunk,
    IngestResponse,
    SourceDocument,
)
from app.services.chunking_service import ChunkingService
from app.services.markdown_chunking_service import MarkdownChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService
from app.utils.document_loader import load_document

logger = logging.getLogger(__name__)

_RETRIEVAL_QUERY_MAX_CHARS = 2000


class RAGService:
    """Orchestrates the full RAG pipeline."""

    # File extensions that use markdown header chunking
    MARKDOWN_EXTENSIONS = {".md"}

    def __init__(self) -> None:
        self._chunking = ChunkingService()
        self._markdown_chunking = MarkdownChunkingService()
        self._embedding = EmbeddingService()
        self._vector_store = VectorStoreService()
        self._llm = LLMService()
        self._settings = get_settings()

    # ──────────────────────────────────────────
    # Document Ingestion
    # ──────────────────────────────────────────

    def ingest_file(self, file_path: str | Path) -> int:
        """
        Ingest a single document file into the vector store.

        Args:
            file_path: Path to the document file.

        Returns:
            Number of chunks created.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Load document content
        text = load_document(file_path)
        if not text.strip():
            logger.warning("File '%s' is empty, skipping.", file_path.name)
            return 0

        # 2. Chunk the text (auto-select strategy based on file type)
        chunker = self._select_chunker(file_path)
        chunks = chunker.chunk_text(
            text=text,
            source=file_path.name,
        )
        if not chunks:
            return 0

        # 3. Generate embeddings
        chunk_texts = [c.content for c in chunks]
        embeddings = self._embedding.embed_texts(chunk_texts)

        # 4. Store in ChromaDB
        self._vector_store.add_documents(
            ids=[c.chunk_id for c in chunks],
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=[c.metadata for c in chunks],
        )

        logger.info(
            "Ingested '%s': %d chunks stored.", file_path.name, len(chunks)
        )
        return len(chunks)

    def _select_chunker(self, file_path: Path):
        """
        Select the appropriate chunking strategy based on file type.

        - .md files → MarkdownChunkingService (split by headers)
        - Other files → ChunkingService (RecursiveCharacterTextSplitter)
        """
        if file_path.suffix.lower() in self.MARKDOWN_EXTENSIONS:
            logger.info("Using MARKDOWN HEADER chunking for '%s'", file_path.name)
            return self._markdown_chunking
        else:
            logger.info("Using RECURSIVE TEXT chunking for '%s'", file_path.name)
            return self._chunking

    def ingest_directory(self, dir_path: str | Path) -> IngestResponse:
        """
        Ingest all supported documents from a directory.

        Args:
            dir_path: Path to the directory containing documents.

        Returns:
            IngestResponse with summary information.
        """
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        supported_extensions = {".txt", ".md", ".pdf", ".docx"}
        total_chunks = 0
        processed_files: list[str] = []

        for file_path in sorted(dir_path.iterdir()):
            if file_path.suffix.lower() in supported_extensions:
                try:
                    n_chunks = self.ingest_file(file_path)
                    total_chunks += n_chunks
                    processed_files.append(file_path.name)
                except Exception as exc:
                    logger.error(
                        "Failed to ingest '%s': %s", file_path.name, exc
                    )

        return IngestResponse(
            message=f"Ingested {len(processed_files)} files with {total_chunks} chunks.",
            total_chunks=total_chunks,
            files_processed=processed_files,
        )

    # ──────────────────────────────────────────
    # Query / Chat
    # ──────────────────────────────────────────

    @staticmethod
    def _build_retrieval_query(question: str, history: list[dict[str, str]]) -> str:
        """
        Build a query string optimized for embedding and retrieval.
        We only embed the current question, because concatenating unrelated 
        previous turns pollutes the semantic meaning of the target query.
        """
        if len(question) <= _RETRIEVAL_QUERY_MAX_CHARS:
            return question.strip()
        return question.strip()[:_RETRIEVAL_QUERY_MAX_CHARS]

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query to uppercase common acronyms since the embedding model
        (dangvantuan/vietnamese-embedding) is highly case-sensitive.
        """
        import re
        replacements = {
            "pt": "PT", "hvt": "HVT", "đbp": "ĐBP", "lhp": "LHP",
            "nct": "NCT", "ntt": "NTT", "uvk": "UVK", "pđl": "PĐL",
            "qt": "QT", "ac": "AC", "nkkn": "NKKN", "hg": "HG",
            "ltk": "LTK", "bh": "BH", "đn": "ĐN", "ct": "CT",
            "gym": "Gym"
        }
        normalized = query
        for k, v in replacements.items():
            pattern = re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE)
            normalized = pattern.sub(v, normalized)
        return normalized

    async def query(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> ChatResponse:
        """
        Process a customer question through the RAG pipeline.

        Steps:
            1. Embed retrieval query (from history + current question)
            2. Retrieve top-k relevant chunks from ChromaDB
            3. Build context from retrieved chunks
            4. Generate answer using LLM (current question + context only)

        Args:
            question: The customer's current question.
            history: Prior turns, excluding the current question.

        Returns:
            ChatResponse with answer and source documents.
        """
        history = history or []
        normalized_question = self._normalize_query(question)
        retrieval_query = self._build_retrieval_query(normalized_question, history)

        # 1. Embed the retrieval query
        query_embedding = self._embedding.embed_query(retrieval_query)

        # 2. Retrieve relevant chunks
        results = self._vector_store.search(
            query_embedding=query_embedding,
            n_results=self._settings.EXERCISE_CONTEXT_LIMIT,
        )

        # 3. Build context and source documents
        context_parts: list[str] = []
        sources: list[SourceDocument] = []

        if results["documents"] and results["documents"][0]:
            for idx, (doc, meta, dist) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                context_parts.append(doc)
                sources.append(
                    SourceDocument(
                        content=doc,
                        source=meta.get("source", "unknown"),
                        chunk_index=meta.get("chunk_index", 0),
                        score=round(1 - dist, 4),  # cosine distance → similarity
                    )
                )

        context = "\n\n".join(context_parts)

        # 4. Generate answer
        if not context.strip():
            answer = (
                "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi "
                "của bạn trong cơ sở dữ liệu. Vui lòng liên hệ bộ phận hỗ trợ "
                "để được giúp đỡ thêm."
            )
        else:
            answer = await self._llm.generate(question=question, context=context)

        return ChatResponse(answer=answer, sources=sources)
