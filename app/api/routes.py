"""
API routes for the RAG chatbot.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CollectionInfoResponse,
    IngestResponse,
)
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["RAG Chatbot"])

# Lazy-initialized RAG service
_rag_service: RAGService | None = None


def _get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


# ──────────────────────────────────────────────
# Chat Endpoint
# ──────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Receive a customer question and return an AI-generated answer
    based on the ingested documents.
    """
    try:
        service = _get_rag_service()
        response = await service.query(
            question=request.question,
            history=[m.model_dump() for m in request.history],
        )
        return response
    except Exception as exc:
        logger.error("Chat error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Đã có lỗi xảy ra khi xử lý câu hỏi.",
        )


# ──────────────────────────────────────────────
# Document Ingestion Endpoints
# ──────────────────────────────────────────────


@router.post("/ingest/directory", response_model=IngestResponse)
async def ingest_directory():
    """
    Ingest all documents from the data/documents/ directory.
    """
    try:
        service = _get_rag_service()
        documents_dir = Path("data/documents")
        if not documents_dir.exists():
            raise HTTPException(
                status_code=404,
                detail="Thư mục data/documents/ không tồn tại.",
            )
        response = service.ingest_directory(documents_dir)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Ingest error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi nạp tài liệu: {str(exc)}",
        )


@router.post("/ingest/upload", response_model=IngestResponse)
async def ingest_upload(file: UploadFile = File(...)):
    """
    Upload and ingest a single document file.
    Supported formats: .txt, .md, .pdf, .docx
    """
    supported = {".txt", ".md", ".pdf", ".docx"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""

    if file_ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng file không hỗ trợ: '{file_ext}'. "
            f"Hỗ trợ: {', '.join(sorted(supported))}",
        )

    try:
        # Save uploaded file to data/documents/
        save_path = Path("data/documents") / file.filename
        save_path.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        save_path.write_bytes(content)

        # Ingest the file
        service = _get_rag_service()
        n_chunks = service.ingest_file(save_path)

        return IngestResponse(
            message=f"Đã nạp file '{file.filename}' thành công.",
            total_chunks=n_chunks,
            files_processed=[file.filename],
        )
    except Exception as exc:
        logger.error("Upload ingest error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi nạp file: {str(exc)}",
        )


# ──────────────────────────────────────────────
# Collection Info
# ──────────────────────────────────────────────


@router.get("/collection/info", response_model=CollectionInfoResponse)
async def get_collection_info():
    """Get information about the vector store collection."""
    try:
        service = _get_rag_service()
        info = service._vector_store.get_collection_info()
        return CollectionInfoResponse(**info)
    except Exception as exc:
        logger.error("Collection info error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Lỗi khi lấy thông tin collection.",
        )


@router.delete("/collection/clear")
async def clear_collection():
    """Clear all documents from the vector store."""
    try:
        service = _get_rag_service()
        service._vector_store.clear_collection()
        return {"message": "Đã xóa toàn bộ dữ liệu trong collection."}
    except Exception as exc:
        logger.error("Clear collection error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Lỗi khi xóa collection.",
        )


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────


@router.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "ok", "message": "RAG Chatbot is running"}
