import logging

import httpx

from app.constants import (
    MAP_GEOCODE_TIMEOUT,
    MAP_GEOCODE_URL,
    MAP_TOP_K_BRANCHES,
    MAP_USER_AGENT,
)
from app.utils.geo_utils import BRANCHES_COORDINATES, STATIC_LOCATION_COORDINATES, haversine_distance

logger = logging.getLogger(__name__)


class MapService:
    def __init__(self) -> None:
        self._headers = {"User-Agent": MAP_USER_AGENT}

    async def geocode_location(self, location_text: str) -> tuple[float, float] | None:
        normalized = location_text.lower().strip()
        if normalized in STATIC_LOCATION_COORDINATES:
            logger.debug("Static coords hit for '%s'", location_text)
            return STATIC_LOCATION_COORDINATES[normalized]

        # Fallback to Nominatim only for unknown locations
        params = {"q": f"{location_text}, Ho Chi Minh, Vietnam", "format": "json", "limit": 1}
        try:
            async with httpx.AsyncClient(timeout=MAP_GEOCODE_TIMEOUT) as client:
                response = await client.get(MAP_GEOCODE_URL, params=params, headers=self._headers)
                response.raise_for_status()
                data = response.json()
                if data and isinstance(data, list):
                    return float(data[0]["lat"]), float(data[0]["lon"])
                return None
        except Exception as exc:
            logger.error("Geocoding failed for '%s': %s", location_text, exc)
            return None

    async def get_closest_branches(
        self, location_text: str, top_k: int = MAP_TOP_K_BRANCHES
    ) -> str | None:
        coords = await self.geocode_location(location_text)
        if not coords:
            return None

        user_lat, user_lon = coords
        ranked = sorted(
            (
                (name, haversine_distance(user_lat, user_lon, c["lat"], c["lng"]))
                for name, c in BRANCHES_COORDINATES.items()
            ),
            key=lambda x: x[1],
        )[:top_k]

        lines = [
            f"\n[HỆ THỐNG MAPS: Khách hàng đang ở '{location_text}'. CHI NHÁNH GẦN NHẤT LÀ {ranked[0][0]}.",
            "Danh sách xếp hạng từ Gần Nhất đến Xa Hơn:",
        ]
        for i, (name, dist) in enumerate(ranked):
            label = "Gần Nhất" if i == 0 else "Xa hơn"
            lines.append(f"Top {i + 1} ({label}): {name} (khoảng cách {dist:.1f} km)")
        lines.append("LLM BẮT BUỘC PHẢI DỰA VÀO ĐÚNG THỨ TỰ NÀY, TUYỆT ĐỐI KHÔNG ĐẢO NGƯỢC THỨ TỰ GẦN XA!]\n")

        return "\n".join(lines)
