"""
Map Service to interact with free Geocoding APIs (Nominatim) and compute distances.
"""

import httpx
import logging
from app.utils.geo_utils import BRANCHES_COORDINATES, haversine_distance

logger = logging.getLogger(__name__)

class MapService:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        # Nominatim requires a valid custom User-Agent to avoid getting 403 Forbidden
        self.headers = {
            "User-Agent": "TheNewGym-SupportBot/1.0"
        }

    async def geocode_location(self, location_text: str) -> tuple[float, float] | None:
        """
        Convert a location text (e.g. 'Thủ Đức') to lat, lng coordinates.
        Uses OpenStreetMap Nominatim Free API.
        """
        # Append Ho Chi Minh context since 13/15 branches are here, giving better accuracy
        # Unless they specify Da Nang or Can Tho, but Nominatim is smart enough.
        query = f"{location_text}, Ho Chi Minh, Vietnam"
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(self.base_url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    lat = float(data[0].get("lat"))
                    lon = float(data[0].get("lon"))
                    return lat, lon
                return None
        except Exception as e:
            logger.error(f"Geocoding failed for '{location_text}': {str(e)}")
            return None

    async def get_closest_branches(self, location_text: str, top_k: int = 3) -> str | None:
        """
        Get a formatted string of the top_k closest branches for RAG context injection.
        """
        coords = await self.geocode_location(location_text)
        if not coords:
            return None
        
        user_lat, user_lon = coords
        
        distances = []
        for name, branch_coords in BRANCHES_COORDINATES.items():
            dist = haversine_distance(
                user_lat, user_lon, 
                branch_coords["lat"], branch_coords["lng"]
            )
            distances.append((name, dist))
            
        distances.sort(key=lambda x: x[1])
        top_branches = distances[:top_k]
        
        # Build the injected sentence for LLM
        injection = f"\n[HỆ THỐNG MAPS VÀ KHOẢNG CÁCH: Khách hàng đang ở '{location_text}'. CHI NHÁNH GẦN NHẤT LÀ {top_branches[0][0]}.\n"
        injection += "Danh sách xếp hạng từ Gần Nhất đến Xa Hơn:\n"
        for i, (name, dist) in enumerate(top_branches):
            if i == 0:
                injection += f"Top 1 (Gần Nhất): {name} (khoảng cách {dist:.1f} km)\n"
            else:
                injection += f"Top {i+1} (Xa hơn): {name} (khoảng cách {dist:.1f} km)\n"
        injection += "LLM BẮT BUỘC PHẢI DỰA VÀO ĐÚNG THỨ TỰ NÀY, TUYỆT ĐỐI KHÔNG ĐẢO NGƯỢC THỨ TỰ GẦN XA!]\n\n"
        
        return injection
