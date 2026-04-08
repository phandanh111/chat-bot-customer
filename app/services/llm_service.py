"""
LLM service.
Communicates with the Ollama API to generate responses
using the ministral-3:8b model.
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# System prompt tuned for Vietnamese customer support
SYSTEM_PROMPT = """Bạn là một trợ lý chăm sóc khách hàng thân thiện và chuyên nghiệp.
Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng dựa trên thông tin được cung cấp trong phần "Ngữ cảnh" bên dưới.

Quy tắc:
1. CHỈ trả lời dựa trên thông tin có trong ngữ cảnh được cung cấp.
2. Nếu ngữ cảnh không chứa đủ thông tin để trả lời, hãy thông báo lịch sự rằng bạn không có thông tin và đề nghị khách hàng liên hệ bộ phận hỗ trợ.
3. Trả lời bằng tiếng Việt, ngắn gọn, rõ ràng và lịch sự.
4. Không bịa đặt hoặc suy đoán thông tin ngoài ngữ cảnh.
5. Nếu có nhiều thông tin liên quan, hãy tổng hợp một cách logic."""


class LLMService:
    """Service for generating responses via Ollama API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.LLM_MODEL
        self._timeout = 120.0  # seconds

    async def generate(self, question: str, context: str) -> str:
        """
        Generate an answer using the LLM with RAG context.

        Args:
            question: The user's question.
            context: Retrieved context from the vector store.

        Returns:
            The generated answer string.
        """
        prompt = self._build_prompt(question, context)

        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 1024,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "").strip()

        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %.1fs", self._timeout)
            return "Xin lỗi, hệ thống đang phản hồi chậm. Vui lòng thử lại sau."

        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP error: %s", exc.response.status_code)
            return "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self._base_url)
            return (
                "Không thể kết nối đến máy chủ AI. "
                "Vui lòng kiểm tra Ollama đang chạy."
            )

    async def health_check(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._base_url)
                return response.status_code == 200
        except Exception:
            return False

    # ──────────────────────────────────────────
    # Private Helpers
    # ──────────────────────────────────────────

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """Build the full prompt with context and question."""
        return (
            f"Ngữ cảnh:\n"
            f"---\n"
            f"{context}\n"
            f"---\n\n"
            f"Câu hỏi của khách hàng: {question}\n\n"
            f"Trả lời:"
        )
