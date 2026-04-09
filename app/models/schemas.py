from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.constants import (
    CHAT_HISTORY_MAX_LENGTH,
    CHAT_MESSAGE_CONTENT_MAX_LENGTH,
    CHAT_QUESTION_MAX_LENGTH,
)


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(...)
    content: str = Field(..., min_length=1, max_length=CHAT_MESSAGE_CONTENT_MAX_LENGTH)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=CHAT_QUESTION_MAX_LENGTH)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=CHAT_HISTORY_MAX_LENGTH)


class SourceDocument(BaseModel):
    content: str
    source: str = Field(default="unknown")
    chunk_index: int = Field(default=0)
    score: Optional[float] = Field(default=None)


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument] = Field(default_factory=list)


class IngestResponse(BaseModel):
    message: str
    total_chunks: int = Field(default=0)
    files_processed: list[str] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    content: str
    metadata: dict = Field(default_factory=dict)
    chunk_id: Optional[str] = None


class CollectionInfoResponse(BaseModel):
    collection_name: str
    total_documents: int
    metadata: Optional[dict] = None
