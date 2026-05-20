"""Google Maps service wrapper (mock implementation).

Loads pre-saved GeoJSON overlays from /data and builds Google Static Maps
API URLs.  A real API key in GOOGLE_MAPS_API_KEY is only needed to render
the static-map image; everything else works without one.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
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


_geocode_cache: dict[str, dict] = {}


def _geocode(location: str) -> dict | None:
    """Query Nominatim (OSM) for coordinates of *location*. Returns {lat, lng} or None."""
    if location in _geocode_cache:
        return _geocode_cache[location]
    try:
        params = urllib.parse.urlencode({"q": location, "format": "json", "limit": 1})
        req = urllib.request.Request(
            f"https://nominatim.openstreetmap.org/search?{params}",
            headers={"User-Agent": "CIRO-App/1.0 (crisis-intelligence)"},
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            results = json.loads(r.read())
        if results:
            coords = {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}
            _geocode_cache[location] = coords
            return coords
    except Exception:
        pass
    return None


def get_overlay(location: str) -> dict:
    """Return the GeoJSON overlay for *location*.

    Lookup order:
      1. Exact key match against JSON files in /data
      2. Partial/fuzzy match (overlay key contained in location string)
      3. Inline hardcoded dict
      4. Nominatim geocode → pin-only overlay with real coordinates
      5. Default fallback (Islamabad)
    """
    key = location.strip().lower()

    # 1. Exact match
    if key in _OVERLAY_FILES:
        return _load_overlay_file(_OVERLAY_FILES[key])

    # 2. Fuzzy match — overlay key is a substring of the location (e.g. "g-10" in "g-10, islamabad")
    for overlay_key, filename in _OVERLAY_FILES.items():
        if overlay_key in key:
            return _load_overlay_file(filename)

    # 3. Inline overlays (exact then fuzzy)
    if key in _INLINE_OVERLAYS:
        return _INLINE_OVERLAYS[key]
    for overlay_key, data in _INLINE_OVERLAYS.items():
        if overlay_key in key:
            return data

    # 4. Nominatim geocoding — real coordinates for any location string
    coords = _geocode(location)
    if coords:
        return {
            **_DEFAULT_OVERLAY,
            "location": location,
            "crisis_pin": coords,
        }

    # 5. Hardcoded fallback
    return {**_DEFAULT_OVERLAY, "location": location}


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
