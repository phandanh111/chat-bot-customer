import logging
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from app.constants import DOCUMENTS_DIR, SUPPORTED_DOCUMENT_EXTENSIONS
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CollectionInfoResponse,
    IngestResponse,
)
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["RAG Chatbot"])

_rag_service: RAGService | None = None


def _get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        return await _get_rag_service().query(
            question=request.question,
            history=[m.model_dump() for m in request.history],
        )
    except Exception as exc:
        logger.error("Chat error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Đã có lỗi xảy ra khi xử lý câu hỏi.")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        stream, sources = await _get_rag_service().stream_query(
            question=request.question,
            history=[m.model_dump() for m in request.history],
        )

        async def event_stream():
            async for token in stream:
                yield json.dumps({"type": "token", "content": token}, ensure_ascii=False) + "\n"
            yield json.dumps(
                {
                    "type": "done",
                    "sources": [source.model_dump() for source in sources],
                },
                ensure_ascii=False,
            ) + "\n"

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")
    except Exception as exc:
        logger.error("Chat stream error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Đã có lỗi xảy ra khi xử lý câu hỏi.")


@router.post("/ingest/directory", response_model=IngestResponse)
async def ingest_directory():
    if not DOCUMENTS_DIR.exists():
        raise HTTPException(status_code=404, detail="Thư mục data/documents/ không tồn tại.")
    try:
        return _get_rag_service().ingest_directory(DOCUMENTS_DIR)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Ingest error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi nạp tài liệu: {str(exc)}")


@router.post("/ingest/upload", response_model=IngestResponse)
async def ingest_upload(file: UploadFile = File(...)):
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng file không hỗ trợ: '{file_ext}'. Hỗ trợ: {', '.join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))}",
        )
    try:
        save_path = DOCUMENTS_DIR / file.filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(await file.read())
        n_chunks = _get_rag_service().ingest_file(save_path)
        return IngestResponse(
            message=f"Đã nạp file '{file.filename}' thành công.",
            total_chunks=n_chunks,
            files_processed=[file.filename],
        )
    except Exception as exc:
        logger.error("Upload ingest error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi nạp file: {str(exc)}")


@router.get("/collection/info", response_model=CollectionInfoResponse)
async def get_collection_info():
    try:
        return CollectionInfoResponse(**_get_rag_service().get_collection_info())
    except Exception as exc:
        logger.error("Collection info error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi khi lấy thông tin collection.")


@router.delete("/collection/clear")
async def clear_collection():
    try:
        _get_rag_service().clear_collection()
        return {"message": "Đã xóa toàn bộ dữ liệu trong collection."}
    except Exception as exc:
        logger.error("Clear collection error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi khi xóa collection.")


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "RAG Chatbot is running"}
