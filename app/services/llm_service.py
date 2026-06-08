import logging
import json
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.constants import (
    LLM_GENERATION_OPTIONS,
    LLM_HISTORY_WINDOW,
    LLM_REQUEST_TIMEOUT,
    LLM_CONNECT_ERROR_REPLY,
    LLM_HTTP_ERROR_REPLY,
    LLM_TIMEOUT_REPLY,
    SUPPORT_EMAIL,
    SUPPORT_HOTLINE,
)
from app.utils.geo_utils import BRANCHES_COORDINATES
from app.utils.prompt_utils import format_chat_history

logger = logging.getLogger(__name__)

_BRANCH_LIST = "\n".join(f"   - {name}" for name in BRANCHES_COORDINATES)

SYSTEM_PROMPT = f"""Bạn là một trợ lý chăm sóc khách hàng thân thiện và chuyên nghiệp của The New Gym.
Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng dựa trên thông tin được cung cấp trong phần "Ngữ cảnh" bên dưới.

Quy tắc QUAN TRỌNG:
1. Nếu ngữ cảnh đã có thông tin, hãy trả lời ĐẦY ĐỦ và CHI TIẾT theo đúng nội dung đó — không được tóm tắt chung chung hay chuyển hướng sang Fanpage khi đã có đủ dữ liệu.
2. DANH SÁCH CHI NHÁNH CHÍNH THỨC CỦA THE NEW GYM (Kiến thức nền tảng bắt buộc):
{_BRANCH_LIST}
   (Nếu khách hỏi chi nhánh ngoài HCM, tự tin mention Biên Hòa, Đà Nẵng, Cần Thơ từ danh sách trên).
3. Nếu khách hỏi thông tin chi tiết (giá, địa chỉ) mà ngữ cảnh KHÔNG có, hãy thông báo lịch sự và đề nghị khách liên hệ Fanpage hoặc hotline {SUPPORT_HOTLINE} / email {SUPPORT_EMAIL}.
4. Trả lời bằng tiếng Việt, ngắn gọn, gạch đầu dòng mạch lạc.
5. "PT" trong ngữ cảnh phòng gym = Huấn Luyện Viên Cá Nhân (Personal Trainer), KHÔNG phải viết tắt của "phòng tập".
6. Với thông tin [HỆ THỐNG MAPS], chỉ được cung cấp TÊN CHI NHÁNH và KHOẢNG CÁCH như đã liệt kê. TUYỆT ĐỐI không được bịa địa chỉ (số nhà, phường, đường) nếu địa chỉ đó không xuất hiện trong ngữ cảnh."""


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.LLM_MODEL
        self._timeout = LLM_REQUEST_TIMEOUT
        self._client = httpx.AsyncClient(timeout=self._timeout)

    async def close(self) -> None:
        await self._client.aclose()

    def _build_payload(self, prompt: str, stream: bool) -> dict:
        return {
            "model": self._model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": stream,
            "think": False,
            "options": LLM_GENERATION_OPTIONS,
        }

    async def generate(self, question: str, context: str, history: list[dict] | None = None) -> str:
        prompt = self._build_prompt(question, context, history)
        payload = self._build_payload(prompt, stream=False)
        try:
            response = await self._client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()

        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %.1fs", self._timeout)
            return LLM_TIMEOUT_REPLY

        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP error: %s", exc.response.status_code)
            return LLM_HTTP_ERROR_REPLY

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self._base_url)
            return LLM_CONNECT_ERROR_REPLY

    async def generate_stream(self, question: str, context: str, history: list[dict] | None = None) -> AsyncIterator[str]:
        prompt = self._build_prompt(question, context, history)
        payload = self._build_payload(prompt, stream=True)
        try:
            async with self._client.stream("POST", f"{self._base_url}/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        return

        except httpx.TimeoutException:
            logger.error("Ollama stream timed out after %.1fs", self._timeout)
            yield LLM_TIMEOUT_REPLY

        except httpx.HTTPStatusError as exc:
            logger.error("Ollama stream HTTP error: %s", exc.response.status_code)
            yield LLM_HTTP_ERROR_REPLY

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self._base_url)
            yield LLM_CONNECT_ERROR_REPLY

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(self._base_url)
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _build_prompt(question: str, context: str, history: list[dict] | None = None) -> str:
        history_block = format_chat_history(history or [], window_size=LLM_HISTORY_WINDOW)
        return (
            f"Ngữ cảnh:\n"
            f"---\n"
            f"{context}\n"
            f"---\n\n"
            f"{history_block}"
            f"Câu hỏi hiện tại của khách hàng: {question}\n\n"
            f"Trả lời:"
        )
