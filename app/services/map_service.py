import logging

import httpx

from app.constants import (
    MAP_CONTEXT_TAG,
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

        params = {"q": f"{location_text}, Vietnam", "format": "json", "limit": 1}
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
            f"\n{MAP_CONTEXT_TAG}: Khách hàng đang ở '{location_text}'. Chi nhánh gần nhất là {ranked[0][0]}.",
            "Danh sách xếp hạng từ gần nhất đến xa hơn:",
        ]
        for i, (name, dist) in enumerate(ranked, start=1):
            lines.append(f"Top {i}: {name} (khoảng cách {dist:.1f} km)")
        lines.append(f"/{MAP_CONTEXT_TAG}\n")

        return "\n".join(lines)
