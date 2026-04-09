import re

RETRIEVAL_QUERY_MAX_CHARS = 2000

SUPPORTED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

MARKDOWN_EXTENSIONS = {".md"}

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

MAP_GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
MAP_USER_AGENT = "TheNewGym-SupportBot/1.0"
MAP_GEOCODE_TIMEOUT = 3.0
MAP_TOP_K_BRANCHES = 3

LLM_REQUEST_TIMEOUT = 120.0

NO_CONTEXT_REPLY = (
    "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi "
    "của bạn trong cơ sở dữ liệu. Vui lòng liên hệ bộ phận hỗ trợ "
    "để được giúp đỡ thêm."
)
