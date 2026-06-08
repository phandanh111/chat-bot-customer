import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import _get_rag_service, router
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


async def _warmup_model(client, base_url: str, model: str) -> None:
    try:
        await client.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": "hi", "stream": False, "think": False, "options": {"num_predict": 1}},
            timeout=60.0,
        )
        logger.info("Warmed up: %s", model)
    except Exception as exc:
        logger.warning("Warmup skipped for %s: %s", model, exc)


async def _warmup_ollama(svc) -> None:
    tasks = [_warmup_model(svc._llm._client, svc._llm._base_url, svc._llm._model)]
    rewriter_model = svc._query_rewriter._model
    if rewriter_model != svc._llm._model:
        tasks.append(_warmup_model(svc._query_rewriter._client, svc._query_rewriter._base_url, rewriter_model))
    await asyncio.gather(*tasks)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading embedding model and services...")
    svc = _get_rag_service()
    logger.info("Embedding model ready. Warming up Ollama...")
    await _warmup_ollama(svc)
    logger.info("Server ready.")
    yield
    await svc._llm.close()
    await svc._query_rewriter.close()
    logger.info("HTTP clients closed.")


app = FastAPI(
    lifespan=lifespan,
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
