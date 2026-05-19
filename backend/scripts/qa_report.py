#!/usr/bin/env python3
"""CIRO backend QA report — run against a live or in-process API.

Usage:
    cd backend && python scripts/qa_report.py
    cd backend && python scripts/qa_report.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


SCENARIOS = [
    ("Urdu flood G-10", {"source": "social", "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"}),
    ("English heatwave", {"source": "social", "text": "48 degrees in Jacobabad, people collapsing on the street"}),
    ("Shahrah blockage", {"source": "social", "text": "Shahrah-e-Faisal completely jammed after truck accident"}),
    ("Low confidence", {"source": "social", "text": "some news from somewhere today"}),
    ("Fire I-9", {"source": "social", "text": "Fire broke out in I-9 industrial area, smoke everywhere"}),
]


def _reset_inprocess() -> None:
    from routers import ingest as ingest_mod
    from routers import simulate as simulate_mod
    from services.cache import analysis_cache
    from services import alert_broadcast
    from services.trace_store import trace_store

    simulate_mod.system_state.traffic_routes = simulate_mod._default_routes()
    simulate_mod.system_state.active_tickets.clear()
    simulate_mod.system_state.sent_alerts.clear()
    simulate_mod.system_state.open_resources.clear()
    simulate_mod._last_simulation = None
    ingest_mod._signal_buffer.clear()
    trace_store.reset()
    analysis_cache.clear()
    alert_broadcast.reset()


def run_inprocess() -> dict:
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    rows = []
    for name, body in SCENARIOS:
        _reset_inprocess()
        t0 = time.perf_counter()
        r = client.post("/pipeline/run", json=body)
        ms = int((time.perf_counter() - t0) * 1000)
        d = r.json() if r.status_code == 200 else {}
        ev = d.get("event", {})
        pl = d.get("plan", {})
        sim = d.get("simulation", {})
        rows.append(
            {
                "scenario": name,
                "http": r.status_code,
                "ms": ms,
                "crisis_type": ev.get("crisis_type"),
                "severity": ev.get("severity"),
                "confidence": ev.get("confidence"),
                "location": ev.get("location"),
                "actions": len(pl.get("actions", [])),
                "alerts": len(sim.get("alerts_sent", [])),
                "tickets": len(sim.get("tickets_created", [])),
                "pass": r.status_code == 200,
            }
        )

    _reset_inprocess()
    client.post("/pipeline/run", json=SCENARIOS[0][1])
    ver = client.get("/simulate/alerts/version").json()
    hist = client.get("/trace/history").json()

    return {
        "mode": "in-process",
        "tests_documented": 139,
        "scenarios": rows,
        "alerts_version": ver.get("version"),
        "trace_history_fields": list(hist[-1].keys()) if hist else [],
    }


def run_remote(base_url: str) -> dict:
    import httpx

    rows = []
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for name, body in SCENARIOS:
            t0 = time.perf_counter()
            r = client.post("/pipeline/run", json=body)
            ms = int((time.perf_counter() - t0) * 1000)
            d = r.json() if r.status_code == 200 else {}
            ev = d.get("event", {})
            rows.append(
                {
                    "scenario": name,
                    "http": r.status_code,
                    "ms": ms,
                    "severity": ev.get("severity"),
                    "confidence": ev.get("confidence"),
                    "pass": r.status_code == 200,
                }
            )
    return {"mode": "remote", "base_url": base_url, "scenarios": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="CIRO QA report")
    parser.add_argument("--base-url", default="", help="If set, hit a running server")
    args = parser.parse_args()

    report = run_remote(args.base_url.rstrip("/")) if args.base_url else run_inprocess()
    print(json.dumps(report, indent=2))

    failed = [r for r in report["scenarios"] if not r.get("pass")]
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
