"""Tests for the Outcome Visualisation endpoint."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _plan(actions):
    return {
        "plan_id": "plan_out",
        "event_id": "evt_out",
        "actions": [
            {
                "action_id": f"act_{i}",
                "type": atype,
                "params": {"target_sector": "G-10", "crisis_type": "flood"},
                "priority": i + 1,
            }
            for i, atype in enumerate(actions)
        ],
    }


def test_outcome_404_before_simulation(client):
    r = client.get("/outcome/summary")
    assert r.status_code == 404


def test_outcome_after_reroute_shows_congestion_reduction(client):
    client.post("/simulate/execute", json=_plan(["reroute_traffic"]))
    body = client.get("/outcome/summary").json()
    assert body["congestion_reduction_pct"] > 0


def test_outcome_vehicles_rerouted_bounded(client):
    client.post("/simulate/execute", json=_plan(["reroute_traffic"]))
    body = client.get("/outcome/summary").json()
    assert 0 <= body["vehicles_rerouted"] <= 800


def test_outcome_min_eta_from_tickets(client):
    client.post(
        "/simulate/execute",
        json=_plan(["dispatch_ambulance", "dispatch_rescue_boats"]),
    )
    body = client.get("/outcome/summary").json()
    assert body["min_eta_minutes"] >= 0


def test_outcome_alerts_dispatched_count(client):
    client.post("/simulate/execute", json=_plan(["send_alert", "send_alert"]))
    body = client.get("/outcome/summary").json()
    assert body["alerts_dispatched"] > 0


def test_outcome_tickets_count(client):
    client.post("/simulate/execute", json=_plan(["dispatch_ambulance"]))
    body = client.get("/outcome/summary").json()
    assert body["tickets_created"] == 1
