"""
Pydantic models for API request/response schemas.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────


class ChatHistoryMessage(BaseModel):
    """One turn in the conversation before the current question."""

    role: Literal["user", "assistant"] = Field(..., description="Who sent this message")
    content: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="Message text",
    )


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The customer's question",
        examples=["Chính sách đổi trả như thế nào?"],
    )
    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=30,
        description="Prior messages (user/assistant), excluding the current question.",
    )


class SourceDocument(BaseModel):
    """A source document chunk used to generate the answer."""

    content: str = Field(..., description="Chunk content")
    source: str = Field(default="unknown", description="Source file name")
    chunk_index: int = Field(default=0, description="Chunk index in source")
    score: Optional[float] = Field(default=None, description="Similarity score")


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""

    answer: str = Field(..., description="Generated answer from the LLM")
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="Source documents used to generate the answer",
    )


# ──────────────────────────────────────────────
# Document Ingestion
# ──────────────────────────────────────────────

class IngestResponse(BaseModel):
    """Response body for the document ingestion endpoint."""

    message: str
    total_chunks: int = Field(default=0, description="Number of chunks created")
    files_processed: list[str] = Field(
        default_factory=list,
        description="List of processed file names",
    )


# ──────────────────────────────────────────────
# Document Chunk (Internal)
# ──────────────────────────────────────────────

class DocumentChunk(BaseModel):
    """Internal model representing a document chunk."""

    content: str
    metadata: dict = Field(default_factory=dict)
    chunk_id: Optional[str] = None


# ──────────────────────────────────────────────
# Collection Info
# ──────────────────────────────────────────────

class CollectionInfoResponse(BaseModel):
    """Response body for collection info endpoint."""

    collection_name: str
    total_documents: int
    metadata: Optional[dict] = None
