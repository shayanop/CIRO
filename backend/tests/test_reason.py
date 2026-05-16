"""Tests for the Reasoning & Analysis Agent.

GROQ_API_KEY is unset in conftest, so every call exercises the fallback
cache path and the in-memory TTL cache.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routers.reason import FALLBACK_CACHE, _get_cached_analysis


def _event(crisis_type: str, severity: str, event_id: str = "evt_reason_test") -> dict:
    return {
        "event_id": event_id,
        "crisis_type": crisis_type,
        "location": "G-10",
        "confidence": 0.9,
        "severity": severity,
        "signals": [],
        "explanation": "test",
    }


@pytest.mark.parametrize("key", list(FALLBACK_CACHE.keys()))
def test_fallback_cache_hit_for_every_key(key):
    crisis_type, severity = key
    result = _get_cached_analysis(crisis_type, severity)
    assert "impact" in result
    assert "summary" in result


def test_fallback_when_crisis_unknown_returns_default():
    result = _get_cached_analysis("imaginary_crisis", "high")
    assert "impact" in result
    assert result["urgency"] == "monitoring"


def test_fallback_picks_any_severity_when_specific_missing():
    # ("accident", "low") is not modeled — should fall back to another severity
    result = _get_cached_analysis("accident", "low")
    assert "impact" in result


def test_analyse_returns_200_and_shape(client):
    r = client.post("/reason/analyse", json=_event("flood", "high"))
    assert r.status_code == 200
    body = r.json()
    for field in ("analysis_id", "event_id", "impact", "summary", "urgency", "affected_population"):
        assert field in body


def test_second_call_cached_is_fast(client):
    payload = _event("flood", "critical", event_id="evt_perf_repeat")
    client.post("/reason/analyse", json=payload)  # warm
    start = time.time()
    r = client.post("/reason/analyse", json=payload)
    elapsed_ms = (time.time() - start) * 1000
    assert r.status_code == 200
    assert elapsed_ms < 200, f"Cached call took {elapsed_ms:.1f}ms"


def test_cache_stats_endpoint(client):
    client.post("/reason/analyse", json=_event("flood", "high", event_id="evt_stat"))
    r = client.get("/reason/cache/stats")
    body = r.json()
    assert body["size"] >= 1
    assert "hits" in body and "misses" in body


def test_cache_clear_resets(client):
    client.post("/reason/analyse", json=_event("flood", "high", event_id="evt_clear"))
    client.post("/reason/cache/clear")
    body = client.get("/reason/cache/stats").json()
    assert body["size"] == 0


def test_distinct_events_produce_distinct_cache_entries(client):
    client.post("/reason/cache/clear")
    client.post("/reason/analyse", json=_event("flood", "high", event_id="evt_a"))
    client.post("/reason/analyse", json=_event("fire", "high", event_id="evt_b"))
    stats = client.get("/reason/cache/stats").json()
    assert stats["size"] == 2
