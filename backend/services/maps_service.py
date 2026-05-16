"""Google Maps service wrapper (mock implementation).

Loads pre-saved GeoJSON overlays from /data and builds Google Static Maps
API URLs.  A real API key in GOOGLE_MAPS_API_KEY is only needed to render
the static-map image; everything else works without one.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Locations whose overlay comes from a JSON file in /data
_OVERLAY_FILES: dict[str, str] = {
    "g-10":              "g10_flood_overlay.json",
    "george town":       "george_town_overlay.json",
    "f-6":               "f6_flood_overlay.json",
    "jacobabad":         "jacobabad_heatwave_overlay.json",
    "shahrah-e-faisal":  "shahrah_faisal_blockage_overlay.json",
    "karachi coast":     "karachi_cyclone_overlay.json",
    "karachi":           "karachi_cyclone_overlay.json",
    "murree":            "murree_landslide_overlay.json",
    "murree road":       "murree_landslide_overlay.json",
    "murree expressway": "murree_landslide_overlay.json",
}

# Hardcoded fallback for locations without a dedicated file
_INLINE_OVERLAYS: dict[str, dict] = {
    "shahrah-e-faisal": {
        "location": "Shahrah-e-Faisal",
        "crisis_pin": {"lat": 24.8674, "lng": 67.0599},
        "affected_polygon": [
            {"lat": 24.870, "lng": 67.055},
            {"lat": 24.870, "lng": 67.065},
            {"lat": 24.864, "lng": 67.065},
            {"lat": 24.864, "lng": 67.055},
            {"lat": 24.870, "lng": 67.055},
        ],
        "primary_route": {
            "name": "Shahrah-e-Faisal",
            "polyline": [
                {"lat": 24.8674, "lng": 67.0599},
                {"lat": 24.8750, "lng": 67.0800},
            ],
            "status": "BLOCKED",
            "color": "#f85149",
        },
        "alternate_route": {
            "name": "Via Korangi Road",
            "polyline": [
                {"lat": 24.8674, "lng": 67.0599},
                {"lat": 24.8500, "lng": 67.0800},
                {"lat": 24.8750, "lng": 67.0800},
            ],
            "status": "ACTIVE",
            "color": "#3fb950",
        },
    }
}

_DEFAULT_OVERLAY: dict = {
    "location": "Unknown",
    "crisis_pin": {"lat": 33.6844, "lng": 73.0479},
    "affected_polygon": [],
    "primary_route": {"name": "Unknown", "polyline": [], "status": "UNKNOWN"},
    "alternate_route": {"name": "Unknown", "polyline": [], "status": "UNKNOWN"},
}


@lru_cache(maxsize=8)
def _load_overlay_file(filename: str) -> dict:
    path = _DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_overlay(location: str) -> dict:
    """Return the GeoJSON overlay for *location*.

    Lookup order:
      1. JSON file in /data (g-10, george town)
      2. Inline hardcoded dict (shahrah-e-faisal)
      3. Default fallback
    """
    key = location.strip().lower()
    filename = _OVERLAY_FILES.get(key)
    if filename:
        return _load_overlay_file(filename)
    return _INLINE_OVERLAYS.get(key, _DEFAULT_OVERLAY)


@lru_cache(maxsize=1)
def get_route_library() -> list:
    """Return the full list of pre-defined alternate route polylines."""
    path = _DATA_DIR / "route_library.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_static_map_url(
    lat: float,
    lng: float,
    zoom: int = 14,
    size: str = "640x400",
    marker_color: str = "red",
) -> str:
    """Construct a Google Static Maps API URL for a crisis pin.

    Requires GOOGLE_MAPS_API_KEY in the environment to actually render.
    Returns a valid URL structure regardless of key presence.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "REQUIRES_API_KEY")
    return (
        "https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}"
        f"&zoom={zoom}"
        f"&size={size}"
        f"&maptype=roadmap"
        f"&markers=color:{marker_color}%7Clabel:C%7C{lat},{lng}"
        f"&key={api_key}"
    )
