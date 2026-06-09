import re
from pathlib import Path

DOCUMENTS_DIR = Path("data/documents")
BRANCHES_DATA_FILE = Path("data/branches.json")

SUPPORTED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
MARKDOWN_EXTENSIONS = {".md"}

CHUNK_SEPARATORS: list[str] = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
MARKDOWN_HEADERS_TO_SPLIT: list[tuple[str, str]] = [("#", "h1"), ("##", "h2"), ("###", "h3")]
MARKDOWN_KNOWN_FIELDS: frozenset[str] = frozenset({
    "Tên club", "Tên", "Tên sản phẩm",
    "Địa chỉ", "Quận", "Tỉnh (Thành phố)", "Tỉnh", "Link",
})

VECTOR_STORE_DISTANCE_METRIC = "cosine"
MIN_RELEVANCE_SCORE: float = 0.35
RETRIEVAL_MAX_CHUNKS_PER_SOURCE: int = 3
RETRIEVAL_QUERY_MAX_CHARS: int = 2000

SHORT_QUERY_THRESHOLD: int = 15
QUERY_REWRITER_HISTORY_WINDOW: int = 4
QUERY_REWRITER_LLM_OPTIONS: dict = {"temperature": 0.0, "num_predict": 30}

LLM_GENERATION_OPTIONS: dict = {"temperature": 0.3, "top_p": 0.9, "num_predict": 600}
LLM_HISTORY_WINDOW: int = 6

CONTEXT_CACHE_MAX_SIZE: int = 256
CONTEXT_CACHE_TTL_SECONDS: int = 3600

RESPONSE_CACHE_MAX_SIZE: int = 128
RESPONSE_CACHE_TTL_SECONDS: int = 1800

LLM_REQUEST_TIMEOUT: float = 120.0
QUERY_REWRITE_TIMEOUT: float = 8.0

MAP_GEOCODE_URL: str = "https://nominatim.openstreetmap.org/search"
MAP_USER_AGENT: str = "TheNewGym-SupportBot/1.0"
MAP_GEOCODE_TIMEOUT: float = 3.0
MAP_TOP_K_BRANCHES: int = 3
MAP_CONTEXT_TAG: str = "[HỆ THỐNG MAPS]"

SUPPORT_HOTLINE: str = "1900 63 69 20"
SUPPORT_EMAIL: str = "cskh@thenewgym.vn"

CHAT_HISTORY_MAX_LENGTH: int = 100
CHAT_QUESTION_MAX_LENGTH: int = 2000
CHAT_MESSAGE_CONTENT_MAX_LENGTH: int = 8000

APP_NAME: str = "RAG Customer Support Chatbot"
APP_VERSION: str = "1.0.0"
APP_HOST: str = "0.0.0.0"
APP_PORT: int = 8000

LOG_FORMAT: str = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

NO_CONTEXT_REPLY: str = (
    "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi "
    "của bạn trong cơ sở dữ liệu. Vui lòng liên hệ bộ phận hỗ trợ "
    "để được giúp đỡ thêm."
)
LLM_TIMEOUT_REPLY: str = "Xin lỗi, hệ thống đang phản hồi chậm. Vui lòng thử lại sau."
LLM_HTTP_ERROR_REPLY: str = "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."
LLM_CONNECT_ERROR_REPLY: str = "Không thể kết nối đến máy chủ AI. Vui lòng kiểm tra Ollama đang chạy."

ACRONYM_NORMALIZATIONS: dict[str, str] = {
    "pt": "PT",
    "hvt": "HVT",
    "đbp": "ĐBP",
    "lhp": "LHP",
    "nct": "NCT",
    "ntt": "NTT",
    "uvk": "UVK",
    "pđl": "PĐL",
    "qt": "QT",
    "ac": "AC",
    "nkkn": "NKKN",
    "hg": "HG",
    "ltk": "LTK",
    "bh": "BH",
    "đn": "ĐN",
    "ct": "CT",
    "gym": "Gym",
}

_RAW_LOCATION_KEYWORDS: list[str] = [
    "thủ đức", "gò vấp", "bình thạnh", "phú nhuận", "tân bình", "tân phú",
    "bình tân", "nhà bè", "bình chánh", "hóc môn", "củ chi",
    "biên hòa", "đà nẵng", "cần thơ",
    "quận một", "quận hai", "quận ba", "quận tư", "quận năm", "quận sáu",
] + [f"quận {i}" for i in range(1, 13)] + [f"q{i}" for i in range(1, 13)]

LOCATION_KEYWORD_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b" + re.escape(kw) + r"\b") for kw in _RAW_LOCATION_KEYWORDS
]
