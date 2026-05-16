"""Tests for the Simulation Engine."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _plan(actions: list[tuple[str, int]]) -> dict:
    return {
        "plan_id": "plan_test",
        "event_id": "evt_test",
        "actions": [
            {
                "action_id": f"act_{i}",
                "type": atype,
                "params": {"target_sector": "G-10", "crisis_type": "flood"},
                "priority": prio,
            }
            for i, (atype, prio) in enumerate(actions)
        ],
    }


def test_reroute_traffic_drops_congestion(client):
    r = client.post("/simulate/execute", json=_plan([("reroute_traffic", 1)]))
    assert r.status_code == 200
    body = r.json()
    assert "reroute_traffic" in body["actions_executed"]
    assert body["state_after"]["avg_congestion"] < body["state_before"]["avg_congestion"]


def test_dispatch_rescue_boats_creates_ticket(client):
    r = client.post("/simulate/execute", json=_plan([("dispatch_rescue_boats", 1)]))
    body = r.json()
    assert len(body["tickets_created"]) == 1
    t = body["tickets_created"][0]
    assert t["unit_dispatched"] == "Rescue Boats"
    assert t["status"] == "dispatched"


def test_dispatch_ambulance_creates_ticket(client):
    r = client.post("/simulate/execute", json=_plan([("dispatch_ambulance", 1)]))
    body = r.json()
    assert body["tickets_created"][0]["unit_dispatched"] == "Rescue 1122"


def test_dispatch_traffic_police_creates_ticket(client):
    r = client.post("/simulate/execute", json=_plan([("dispatch_traffic_police", 1)]))
    body = r.json()
    assert body["tickets_created"][0]["unit_dispatched"] == "Traffic Police"


def test_send_alert_creates_alert(client):
    r = client.post("/simulate/execute", json=_plan([("send_alert", 1)]))
    body = r.json()
    assert len(body["alerts_sent"]) == 1
    assert body["alerts_sent"][0]["recipients_count"] > 0


def test_open_cooling_centre_registers_resource(client):
    r = client.post("/simulate/execute", json=_plan([("open_cooling_centres", 1)]))
    assert r.status_code == 200
    state = client.get("/simulate/state").json()
    assert any("Cooling Centre" in res for res in state["open_resources"])


def test_unknown_action_skipped(client):
    r = client.post("/simulate/execute", json=_plan([("not_a_real_action", 1)]))
    assert r.status_code == 200
    body = r.json()
    assert body["actions_executed"] == []


def test_reset_clears_state(client):
    client.post("/simulate/execute", json=_plan([("dispatch_ambulance", 1), ("send_alert", 2)]))
    client.post("/simulate/reset")
    state = client.get("/simulate/state").json()
    assert state["active_tickets_count"] == 0
    assert state["sent_alerts_count"] == 0
    assert state["open_resources"] == []


def test_before_after_snapshot_captured(client):
    r = client.post("/simulate/execute", json=_plan([("reroute_traffic", 1)]))
    body = r.json()
    assert "state_before" in body and "state_after" in body
    assert "avg_congestion" in body["state_before"]
    assert "avg_congestion" in body["state_after"]


def test_tickets_endpoint_lists_tickets(client):
    client.post("/simulate/execute", json=_plan([("dispatch_ambulance", 1)]))
    r = client.get("/simulate/tickets")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_alerts_endpoint_lists_alerts(client):
    client.post("/simulate/execute", json=_plan([("send_alert", 1)]))
    r = client.get("/simulate/alerts")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_patch_ticket_status(client):
    client.post("/simulate/execute", json=_plan([("dispatch_ambulance", 1)]))
    tid = client.get("/simulate/tickets").json()[0]["ticket_id"]
    r = client.patch(f"/simulate/tickets/{tid}/status", params={"status": "resolved"})
    assert r.status_code == 200
    assert r.json()["new_status"] == "resolved"


def test_patch_unknown_ticket_returns_404(client):
    r = client.patch("/simulate/tickets/tic_doesnotexist/status", params={"status": "resolved"})
    assert r.status_code == 404
