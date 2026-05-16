"""Mock data endpoints for CIRO demo.

Serves simulated social signals, weather data, and traffic data from
pre-saved JSON files under ``/data/``.
"""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["Mock Data"])

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(filename: str) -> dict | list:
    with open(_DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _get_social_signals() -> list:
    return _load_json("social_signals.json")


@lru_cache(maxsize=1)
def _get_weather_data() -> dict:
    return _load_json("weather_mock.json")


@lru_cache(maxsize=1)
def _get_traffic_data() -> dict:
    return _load_json("traffic_mock.json")


@router.get("/social", summary="Random mock social media signal")
async def get_social_signal():
    """Return one random social media signal from the mock pool."""
    signals = _get_social_signals()
    return random.choice(signals)


@router.get("/weather", summary="Mock weather alert JSON")
async def get_weather():
    """Return the full mock OpenWeatherMap-style weather data."""
    return _get_weather_data()


@router.get("/traffic", summary="Mock traffic congestion data")
async def get_traffic():
    """Return mock traffic route congestion data."""
    return _get_traffic_data()
