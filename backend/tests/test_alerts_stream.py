"""Tests for alert broadcast version and SSE stream."""

from __future__ import annotations


def test_alerts_version_increments_after_pipeline(client):
    v0 = client.get("/simulate/alerts/version").json()["version"]
    client.post(
        "/pipeline/run",
        json={"source": "social", "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"},
    )
    v1 = client.get("/simulate/alerts/version").json()
    assert v1["version"] > v0
    assert v1["alerts_count"] >= 1


def test_alerts_stream_returns_event_stream(client):
    client.post("/pipeline/run", json={"source": "social", "text": "fire in I-9 smoke"})
    r = client.get("/simulate/alerts/stream", params={"once": True})
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
    assert "data:" in r.text
    assert "alerts" in r.text
