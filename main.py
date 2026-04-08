"""
RAG Customer Support Chatbot - FastAPI Application

Entry point for the application.
Run with: python main.py
"""

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings

# ──────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="RAG Customer Support Chatbot",
    description=(
        "Chatbot chăm sóc khách hàng sử dụng Retrieval Augmented Generation. "
        "Trả lời câu hỏi dựa trên tài liệu đã được nạp vào hệ thống."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routes
app.include_router(router)


# ──────────────────────────────────────────────
# Root Endpoint
# ──────────────────────────────────────────────


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Customer Support Chatbot",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting RAG Customer Support Chatbot...")
    logger.info("LLM Model: %s", settings.LLM_MODEL)
    logger.info("Embed Model: %s", settings.EMBED_MODEL)
    logger.info("Ollama URL: %s", settings.OLLAMA_BASE_URL)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
