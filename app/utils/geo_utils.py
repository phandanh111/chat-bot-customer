import json
import logging
import math

from app.constants import BRANCHES_DATA_FILE

logger = logging.getLogger(__name__)


def _load_branches_data() -> dict:
    try:
        with open(BRANCHES_DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("branches.json not found at %s — using empty data", BRANCHES_DATA_FILE)
        return {"branches": [], "static_location_coordinates": {}}


_data = _load_branches_data()

STATIC_LOCATION_COORDINATES: dict[str, tuple[float, float]] = {
    k: (float(v[0]), float(v[1]))
    for k, v in _data.get("static_location_coordinates", {}).items()
}

BRANCHES_COORDINATES: dict[str, dict[str, float]] = {
    b["name"]: {"lat": float(b["lat"]), "lng": float(b["lng"])}
    for b in _data.get("branches", [])
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * math.asin(math.sqrt(a)) * 6371
