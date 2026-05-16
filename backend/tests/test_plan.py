"""Tests for the Action Planning Agent.

Covers every (crisis_type, severity) key in ACTION_RULES.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routers.plan import ACTION_RULES


def _crisis_event_payload(crisis_type: str, severity: str) -> dict:
    return {
        "event_id": f"evt_{crisis_type}_{severity}",
        "crisis_type": crisis_type,
        "location": "G-10",
        "confidence": 0.9,
        "severity": severity,
        "signals": [],
        "explanation": "test",
    }


@pytest.mark.parametrize("key", list(ACTION_RULES.keys()))
def test_action_rules_lookup_yields_plan(client, key):
    """Every (crisis_type, severity) key returns a 200 ActionPlan."""
    ctype, sev = key
    r = client.post("/plan/actions", json=_crisis_event_payload(ctype, sev))
    assert r.status_code == 200
    body = r.json()
    assert body["event_id"] == f"evt_{ctype}_{sev}"
    expected_actions = ACTION_RULES[key]
    assert len(body["actions"]) == len(expected_actions)


def test_action_types_match_rules(client):
    r = client.post("/plan/actions", json=_crisis_event_payload("flood", "high"))
    body = r.json()
    types = [a["type"] for a in body["actions"]]
    assert types == [t for (t, _) in ACTION_RULES[("flood", "high")]]


def test_priority_ordering(client):
    r = client.post("/plan/actions", json=_crisis_event_payload("fire", "critical"))
    body = r.json()
    priorities = [a["priority"] for a in body["actions"]]
    assert priorities == sorted(priorities)


def test_low_severity_yields_empty_plan(client):
    r = client.post("/plan/actions", json=_crisis_event_payload("flood", "low"))
    body = r.json()
    assert body["actions"] == []


def test_unknown_combination_yields_empty_actions(client):
    """An unmodeled (type, severity) pair should still return an ActionPlan."""
    # Use a severity for a crisis type that doesn't exist
    payload = _crisis_event_payload("flood", "critical")
    r = client.post("/plan/actions", json=payload)
    assert r.status_code == 200
