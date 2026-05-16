"""Maps overlay endpoint – GET /maps/crisis-overlay

Stub router. Full implementation by Hasnain.
Returns pre-saved GeoJSON for crisis visualisation on the map.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/maps", tags=["Maps"])

# Pre-saved GeoJSON overlays for demo scenarios
_OVERLAYS = {
    "G-10": {
        "crisis_pin": {"lat": 33.6844, "lng": 73.0479},
        "affected_polygon": [
            {"lat": 33.690, "lng": 73.040},
            {"lat": 33.690, "lng": 73.060},
            {"lat": 33.678, "lng": 73.060},
            {"lat": 33.678, "lng": 73.040},
        ],
        "primary_route": {
            "name": "G-10 to Blue Area",
            "polyline": [
                {"lat": 33.6844, "lng": 73.0479},
                {"lat": 33.6950, "lng": 73.0580},
                {"lat": 33.7100, "lng": 73.0600},
            ],
            "status": "BLOCKED",
        },
        "alternate_route": {
            "name": "Via Margalla Road",
            "polyline": [
                {"lat": 33.6844, "lng": 73.0479},
                {"lat": 33.7200, "lng": 73.0700},
                {"lat": 33.7100, "lng": 73.0600},
            ],
            "status": "ACTIVE",
        },
    },
    "george town": {
        "crisis_pin": {"lat": 24.8607, "lng": 67.0011},
        "affected_polygon": [
            {"lat": 24.865, "lng": 66.995},
            {"lat": 24.865, "lng": 67.010},
            {"lat": 24.855, "lng": 67.010},
            {"lat": 24.855, "lng": 66.995},
        ],
        "primary_route": {
            "name": "George Town to Saddar",
            "polyline": [
                {"lat": 24.8607, "lng": 67.0011},
                {"lat": 24.8550, "lng": 67.0200},
            ],
            "status": "BLOCKED",
        },
        "alternate_route": {
            "name": "Via M.A. Jinnah Road",
            "polyline": [
                {"lat": 24.8607, "lng": 67.0011},
                {"lat": 24.8700, "lng": 67.0300},
                {"lat": 24.8550, "lng": 67.0200},
            ],
            "status": "ACTIVE",
        },
    },
    "shahrah-e-faisal": {
        "crisis_pin": {"lat": 24.8674, "lng": 67.0599},
        "affected_polygon": [
            {"lat": 24.870, "lng": 67.055},
            {"lat": 24.870, "lng": 67.065},
            {"lat": 24.864, "lng": 67.065},
            {"lat": 24.864, "lng": 67.055},
        ],
        "primary_route": {
            "name": "Shahrah-e-Faisal",
            "polyline": [
                {"lat": 24.8674, "lng": 67.0599},
                {"lat": 24.8750, "lng": 67.0800},
            ],
            "status": "BLOCKED",
        },
        "alternate_route": {
            "name": "Via Korangi Road",
            "polyline": [
                {"lat": 24.8674, "lng": 67.0599},
                {"lat": 24.8500, "lng": 67.0800},
                {"lat": 24.8750, "lng": 67.0800},
            ],
            "status": "ACTIVE",
        },
    },
}

# Default overlay for unknown locations
_DEFAULT_OVERLAY = {
    "crisis_pin": {"lat": 33.6844, "lng": 73.0479},
    "affected_polygon": [],
    "primary_route": {"name": "Unknown", "polyline": [], "status": "UNKNOWN"},
    "alternate_route": {"name": "Unknown", "polyline": [], "status": "UNKNOWN"},
}


@router.get("/crisis-overlay", summary="GeoJSON crisis overlay")
async def get_crisis_overlay(location: str = "G-10"):
    """Return a pre-saved GeoJSON overlay for the specified location.

    Includes crisis pin, affected area polygon, blocked primary route,
    and recommended alternate route.
    """
    overlay = _OVERLAYS.get(location.lower(), _OVERLAYS.get(location.upper(), _DEFAULT_OVERLAY))
    return overlay
