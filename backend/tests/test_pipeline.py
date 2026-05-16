"""End-to-end pipeline tests via FastAPI TestClient.

Each test exercises POST /pipeline/run with one of the demo scenarios
and asserts the contract documented in docs/PIPELINE_CONTRACT.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _assert_pipeline_shape(body: dict) -> None:
    for key in ("run_id", "batch", "event", "analysis", "plan", "simulation"):
        assert key in body, f"missing key {key}"
    assert body["event"]["event_id"].startswith("evt_")
    assert body["plan"]["plan_id"].startswith("plan_")
    assert "actions_executed" in body["simulation"]


def test_pipeline_happy_path_urdu_flood(client):
    r = client.post(
        "/pipeline/run",
        json={"source": "social", "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"},
    )
    assert r.status_code == 200
    body = r.json()
    _assert_pipeline_shape(body)
    assert body["event"]["crisis_type"] == "flood"
    assert body["event"]["location"] == "G-10"


def test_pipeline_english_heatwave(client):
    r = client.post(
        "/pipeline/run",
        json={
            "source": "social",
            "text": "48 degrees in Jacobabad, people collapsing on the street",
        },
    )
    assert r.status_code == 200
    body = r.json()
    _assert_pipeline_shape(body)
    assert body["event"]["crisis_type"] == "heatwave"


def test_pipeline_blockage_shahrah(client):
    r = client.post(
        "/pipeline/run",
        json={
            "source": "traffic",
            "text": "Shahrah-e-Faisal completely jammed after truck accident",
        },
    )
    assert r.status_code == 200
    body = r.json()
    _assert_pipeline_shape(body)
    assert body["event"]["crisis_type"] in {"blockage", "accident"}


def test_pipeline_low_confidence_vague_signal(client):
    r = client.post(
        "/pipeline/run",
        json={"source": "social", "text": "some news from somewhere today"},
    )
    assert r.status_code == 200
    body = r.json()
    _assert_pipeline_shape(body)
    assert body["event"]["confidence"] < 0.6


def test_pipeline_fire_scenario(client):
    r = client.post(
        "/pipeline/run",
        json={"source": "social", "text": "Aag lag gayi hai dukan mein G-9, smoke phailega"},
    )
    body = r.json()
    _assert_pipeline_shape(body)
    assert body["event"]["crisis_type"] == "fire"


def test_pipeline_completes_trace_run(client):
    client.post("/pipeline/run", json={"source": "social", "text": "flood G-10"})
    trace = client.get("/trace/latest").json()
    assert trace["status"] == "complete"
    assert len(trace["steps"]) >= 4
