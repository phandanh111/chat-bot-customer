import logging

import httpx

from app.config import get_settings
from app.constants import (
    LLM_REQUEST_TIMEOUT,
)
from app.utils.geo_utils import BRANCHES_COORDINATES

logger = logging.getLogger(__name__)

_BRANCH_LIST = "\n".join(f"   - {name}" for name in BRANCHES_COORDINATES)

SYSTEM_PROMPT = f"""Bạn là một trợ lý chăm sóc khách hàng thân thiện và chuyên nghiệp của The New Gym.
Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng dựa trên thông tin được cung cấp trong phần "Ngữ cảnh" bên dưới.

Quy tắc QUAN TRỌNG:
1. CHỈ trả lời chi tiết dựa trên thông tin có trong ngữ cảnh.
2. DANH SÁCH CHI NHÁNH CHÍNH THỨC CỦA THE NEW GYM (Kiến thức nền tảng bắt buộc):
{_BRANCH_LIST}
   (Nếu khách hỏi chi nhánh ngoài HCM, tự tin mention Biên Hòa, Đà Nẵng, Cần Thơ từ danh sách trên).
3. Nếu khách hỏi thông tin chi tiết (giá, địa chỉ) mà ngữ cảnh không có, hãy thông báo lịch sự và đề nghị khách liên hệ Fanpage.
4. Trả lời bằng tiếng Việt, ngắn gọn, gạch đầu dòng mạch lạc."""


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.LLM_MODEL
        self._timeout = LLM_REQUEST_TIMEOUT

    async def generate(self, question: str, context: str) -> str:
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
                return response.json().get("response", "").strip()

        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %.1fs", self._timeout)
            return "Xin lỗi, hệ thống đang phản hồi chậm. Vui lòng thử lại sau."

        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP error: %s", exc.response.status_code)
            return "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self._base_url)
            return "Không thể kết nối đến máy chủ AI. Vui lòng kiểm tra Ollama đang chạy."

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._base_url)
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        return (
            f"Ngữ cảnh:\n"
            f"---\n"
            f"{context}\n"
            f"---\n\n"
            f"Câu hỏi của khách hàng: {question}\n\n"
            f"Trả lời:"
        )
