"""
Geographical utilities: coordinates for branches and Haversine distance algorithm.
"""

import math

# Hardcoded approximate coordinates for the 15 official branches.
# Providing a static list bypasses the need to Geocode our own branches during runtime.
BRANCHES_COORDINATES = {
    "The New Gym Hoàng Văn Thụ (Tân Bình)": {"lat": 10.7963, "lng": 106.6622},
    "The New Gym Điện Biên Phủ (Quận 10)": {"lat": 10.7712, "lng": 106.6781},
    "The New Gym Lê Hồng Phong (Quận 5)": {"lat": 10.7601, "lng": 106.6723},
    "The New Gym Nguyễn Chí Thanh (Quận 10)": {"lat": 10.7610, "lng": 106.6620},
    "The New Gym Nguyễn Thị Thập (Quận 7)": {"lat": 10.7381, "lng": 106.7115},
    "The New Gym Ung Văn Khiêm (Bình Thạnh)": {"lat": 10.8062, "lng": 106.7151},
    "The New Gym Phan Đăng Lưu (Phú Nhuận)": {"lat": 10.8034, "lng": 106.6853},
    "The New Gym Quang Trung (Gò Vấp)": {"lat": 10.8401, "lng": 106.6504},
    "The New Gym Âu Cơ (Tân Phú)": {"lat": 10.7812, "lng": 106.6393},
    "The New Gym Nam Kỳ Khởi Nghĩa (Quận 3)": {"lat": 10.7845, "lng": 106.6852},
    "The New Gym Hậu Giang (Quận 6)": {"lat": 10.7481, "lng": 106.6364},
    "The New Gym Lý Thường Kiệt (Quận 11)": {"lat": 10.7682, "lng": 106.6575},
    "The New Gym Biên Hòa (Đồng Nai)": {"lat": 10.9572, "lng": 106.8423},
    "The New Gym Đà Nẵng": {"lat": 16.0544, "lng": 108.2021},
    "The New Gym Cần Thơ": {"lat": 10.0451, "lng": 105.7468},
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles.
    return c * r
