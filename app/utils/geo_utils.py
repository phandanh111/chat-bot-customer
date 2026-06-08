import logging
import math

logger = logging.getLogger(__name__)

# Tọa độ cứng cho các quận/huyện/thành phố thường gặp — không cần gọi Nominatim
STATIC_LOCATION_COORDINATES: dict[str, tuple[float, float]] = {
    # TP.HCM - các quận nội thành
    "quận 1": (10.7769, 106.7009),
    "q1": (10.7769, 106.7009),
    "quận 2": (10.7867, 106.7519),
    "q2": (10.7867, 106.7519),
    "quận 3": (10.7799, 106.6888),
    "q3": (10.7799, 106.6888),
    "quận 4": (10.7574, 106.7044),
    "q4": (10.7574, 106.7044),
    "quận 5": (10.7551, 106.6647),
    "q5": (10.7551, 106.6647),
    "quận 6": (10.7487, 106.6348),
    "q6": (10.7487, 106.6348),
    "quận 7": (10.7350, 106.7218),
    "q7": (10.7350, 106.7218),
    "quận 8": (10.7235, 106.6285),
    "q8": (10.7235, 106.6285),
    "quận 9": (10.8410, 106.8150),
    "q9": (10.8410, 106.8150),
    "quận 10": (10.7740, 106.6652),
    "q10": (10.7740, 106.6652),
    "quận 11": (10.7620, 106.6505),
    "q11": (10.7620, 106.6505),
    "quận 12": (10.8670, 106.6430),
    "q12": (10.8670, 106.6430),
    # Thành phố Thủ Đức (gộp Q2, Q9, Thủ Đức cũ)
    "thủ đức": (10.8661, 106.7843),
    "quận thủ đức": (10.8661, 106.7843),
    # Các quận/huyện khác HCM
    "bình thạnh": (10.8120, 106.7148),
    "quận bình thạnh": (10.8120, 106.7148),
    "phú nhuận": (10.7990, 106.6799),
    "quận phú nhuận": (10.7990, 106.6799),
    "tân bình": (10.8014, 106.6529),
    "quận tân bình": (10.8014, 106.6529),
    "tân phú": (10.7908, 106.6250),
    "quận tân phú": (10.7908, 106.6250),
    "gò vấp": (10.8384, 106.6652),
    "quận gò vấp": (10.8384, 106.6652),
    "bình tân": (10.7636, 106.6044),
    "quận bình tân": (10.7636, 106.6044),
    "nhà bè": (10.6977, 106.7342),
    "huyện nhà bè": (10.6977, 106.7342),
    "bình chánh": (10.6880, 106.5890),
    "huyện bình chánh": (10.6880, 106.5890),
    "hóc môn": (10.8917, 106.5942),
    "huyện hóc môn": (10.8917, 106.5942),
    "củ chi": (11.0037, 106.4985),
    "huyện củ chi": (11.0037, 106.4985),
    # Tỉnh/thành ngoài HCM
    "biên hòa": (10.9441, 106.8232),
    "đồng nai": (10.9441, 106.8232),
    "đà nẵng": (16.0544, 108.2021),
    "cần thơ": (10.0451, 105.7468),
}

BRANCHES_COORDINATES: dict[str, dict[str, float]] = {
    "The New Gym Hoàng Văn Thụ (Tân Bình)":      {"lat": 10.7963, "lng": 106.6622},
    "The New Gym Điện Biên Phủ (Quận 10)":        {"lat": 10.7712, "lng": 106.6781},
    "The New Gym Lê Hồng Phong (Quận 5)":         {"lat": 10.7601, "lng": 106.6723},
    "The New Gym Nguyễn Chí Thanh (Quận 10)":     {"lat": 10.7610, "lng": 106.6620},
    "The New Gym Nguyễn Thị Thập (Quận 7)":       {"lat": 10.7381, "lng": 106.7115},
    "The New Gym Ung Văn Khiêm (Bình Thạnh)":     {"lat": 10.8062, "lng": 106.7151},
    "The New Gym Phan Đăng Lưu (Phú Nhuận)":      {"lat": 10.8034, "lng": 106.6853},
    "The New Gym Quang Trung (Gò Vấp)":           {"lat": 10.8401, "lng": 106.6504},
    "The New Gym Âu Cơ (Tân Phú)":               {"lat": 10.7812, "lng": 106.6393},
    "The New Gym Nam Kỳ Khởi Nghĩa (Quận 3)":    {"lat": 10.7845, "lng": 106.6852},
    "The New Gym Hậu Giang (Quận 6)":             {"lat": 10.7481, "lng": 106.6364},
    "The New Gym Lý Thường Kiệt (Quận 11)":       {"lat": 10.7682, "lng": 106.6575},
    "The New Gym Biên Hòa (Đồng Nai)":            {"lat": 10.9572, "lng": 106.8423},
    "The New Gym Đà Nẵng":                        {"lat": 16.0544, "lng": 108.2021},
    "The New Gym Cần Thơ":                        {"lat": 10.0451, "lng": 105.7468},
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * math.asin(math.sqrt(a)) * 6371
