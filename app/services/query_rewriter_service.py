import logging
import re

import httpx

from app.config import get_settings
from app.constants import QUERY_REWRITE_TIMEOUT

logger = logging.getLogger(__name__)

_SHORT_QUERY_THRESHOLD = 15

# Từ tham chiếu ngữ cảnh — dấu hiệu câu hỏi follow-up cần history để hiểu
_REFERENCE_PATTERN = re.compile(
    r"\b(thế|vậy|còn|kia|đấy|nó|cái đó|cái kia|cái này|"
    r"loại đó|gói đó|gói kia|chi nhánh đó|ở đó|ở đây|chỗ đó|chỗ đây)\b",
    re.IGNORECASE,
)

_SYSTEM_STANDALONE = (
    "Bạn là công cụ viết lại câu hỏi thành query tìm kiếm độc lập cho phòng gym The New Gym. "
    "Dựa vào lịch sử hội thoại (nếu có), viết lại câu hỏi thành một câu hoàn chỉnh, tự hiểu được "
    "mà không cần đọc lịch sử. Chỉ trả về câu query đã viết lại, không giải thích."
)

# Các pattern xác định → trả về ngay, KHÔNG gọi LLM
_STATIC_EXPANSIONS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"^(giá\s*(gym|tập|vé)?\s*\??)$", re.IGNORECASE),
        "giá gói tập tự tập hội viên 1 tháng 3 tháng 6 tháng The New Gym",
    ),
    (
        re.compile(r"^(có\s+pt\s*(không|ko|k)?\s*\??|pt\s+có\s*không\s*\??)$", re.IGNORECASE),
        "gói PT Silver Gold Diamond Platinum tại The New Gym giá bao nhiêu",
    ),
    (
        re.compile(r"^(pt\s+(giá|bao nhiêu)\s*\??|giá\s+pt\s*\??)$", re.IGNORECASE),
        "gói PT Silver Gold Diamond Platinum tại The New Gym giá bao nhiêu",
    ),
]

_EXAMPLES_STANDALONE = (
    "Ví dụ với lịch sử:\n"
    "  Lịch sử: Khách: Gói PT Gold gồm gì? / Bot: 8 buổi, 4.999.000 VNĐ\n"
    "  Câu hỏi: 'Thế còn Platinum thì sao?'\n"
    "  → Gói PT Platinum tại The New Gym bao gồm những gì, giá bao nhiêu?\n\n"
    "  Lịch sử: Khách: Chi nhánh Quận 5 ở đâu? / Bot: 197C Lê Hồng Phong\n"
    "  Câu hỏi: 'Giờ mở cửa ở đó thế nào?'\n"
    "  → Giờ mở cửa chi nhánh Lê Hồng Phong Quận 5 The New Gym\n\n"
    "Ví dụ không có lịch sử:\n"
    "  địa chỉ? → danh sách địa chỉ các chi nhánh The New Gym\n"
    "  gym ở đâu? → danh sách chi nhánh The New Gym ở đâu\n"
)


class QueryRewriterService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.LLM_MODEL
        self._client = httpx.AsyncClient(timeout=QUERY_REWRITE_TIMEOUT)

    async def close(self) -> None:
        await self._client.aclose()

    async def rewrite(self, query: str, history: list[dict] | None = None) -> str:
        q_stripped = query.strip()
        for pattern, expansion in _STATIC_EXPANSIONS:
            if pattern.match(q_stripped):
                logger.debug("Static expansion: '%s' → '%s'", query, expansion)
                return expansion

        is_short = len(q_stripped) < _SHORT_QUERY_THRESHOLD
        has_reference = bool(_REFERENCE_PATTERN.search(query))

        if not is_short and not has_reference:
            return query

        history_block = ""
        if history:
            recent = history[-4:]
            lines = [
                f"{'Khách' if m['role'] == 'user' else 'Bot'}: {m['content'][:200]}"
                for m in recent
            ]
            history_block = "Lịch sử hội thoại:\n" + "\n".join(lines) + "\n\n"

        prompt = (
            f"{_EXAMPLES_STANDALONE}"
            f"{history_block}"
            f"Câu hỏi hiện tại: {query}\n"
            f"Query tìm kiếm độc lập:"
        )
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": _SYSTEM_STANDALONE,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.0, "num_predict": 30},
        }
        try:
            response = await self._client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            rewritten = response.json().get("response", "").strip().strip("\"'").strip()
            if rewritten:
                logger.debug("Query rewritten: '%s' → '%s'", query, rewritten)
                return rewritten
        except Exception as exc:
            logger.warning("Query rewrite failed, using original: %s", exc)

        return query
