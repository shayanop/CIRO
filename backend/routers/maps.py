"""Maps endpoints – crisis overlay and static map.

GET /maps/crisis-overlay?location=G-10
    Returns pre-saved GeoJSON (crisis pin, affected polygon, routes).
    Data is loaded from /data/*.json via maps_service.

GET /maps/static-map?location=G-10
    Returns a Google Static Maps API URL for the crisis pin.
    Requires GOOGLE_MAPS_API_KEY in .env to render the actual image.

GET /maps/routes
    Returns the full route library (5 alternate polylines).
"""

from __future__ import annotations

from fastapi import APIRouter

from services.maps_service import build_static_map_url, get_overlay, get_route_library

router = APIRouter(prefix="/maps", tags=["Maps"])


@router.get("/crisis-overlay", summary="GeoJSON crisis overlay for a location")
async def get_crisis_overlay(location: str = "G-10"):
    """Return a pre-saved GeoJSON overlay for the specified location.

    Includes crisis pin, affected area polygon, blocked primary route,
    and recommended alternate route.  Supported locations: G-10,
    George Town, Shahrah-e-Faisal.
    """
    return get_overlay(location)


@router.get("/static-map", summary="Google Static Maps URL for a crisis pin")
async def get_static_map(location: str = "G-10", zoom: int = 14):
    """Return a Google Static Maps API URL centred on the crisis pin.

    The URL is valid but requires a real GOOGLE_MAPS_API_KEY in the
    environment (.env file) to render the map image.
    """
    overlay = get_overlay(location)
    pin = overlay.get("crisis_pin", {"lat": 33.6844, "lng": 73.0479})
    lat, lng = pin["lat"], pin["lng"]

    url = build_static_map_url(lat=lat, lng=lng, zoom=zoom)
    return {
        "location": location,
        "crisis_pin": pin,
        "static_map_url": url,
        "note": "Set GOOGLE_MAPS_API_KEY in .env to render the map image.",
    }


@router.get("/routes", summary="Pre-defined alternate route library")
async def get_routes():
    """Return all pre-defined alternate route polylines from the route library."""
    return get_route_library()
