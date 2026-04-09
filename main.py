import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.constants import (
    APP_HOST,
    APP_NAME,
    APP_PORT,
    APP_VERSION,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=APP_NAME,
    description=(
        "Chatbot chăm sóc khách hàng sử dụng Retrieval Augmented Generation. "
        "Trả lời câu hỏi dựa trên tài liệu đã được nạp vào hệ thống."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"name": APP_NAME, "version": APP_VERSION, "docs": "/docs", "health": "/api/health"}


if __name__ == "__main__":
    logger.info("Starting %s...", APP_NAME)
    logger.info("LLM Model: %s", settings.LLM_MODEL)
    logger.info("Embed Model: %s", settings.EMBED_MODEL)
    logger.info("Ollama URL: %s", settings.OLLAMA_BASE_URL)
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)
