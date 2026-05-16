"""Tests for the trace_store and /trace/* endpoints."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.trace_store import TraceStore


def test_start_run_returns_unique_id():
    ts = TraceStore()
    run_id = ts.start_run("hello")
    assert run_id.startswith("run_")
    latest = ts.get_latest()
    assert latest["run_id"] == run_id
    assert latest["status"] == "running"


def test_log_step_appends_and_accumulates_duration():
    ts = TraceStore()
    rid = ts.start_run("x")
    ts.log_step(rid, "a", "step1", {}, {}, duration_ms=10)
    ts.log_step(rid, "b", "step2", {}, {}, duration_ms=25)
    latest = ts.get_latest()
    assert len(latest["steps"]) == 2
    assert latest["total_duration_ms"] == 35


def test_complete_run_archives():
    ts = TraceStore()
    rid = ts.start_run("y")
    ts.complete_run(rid, outcome="done")
    latest = ts.get_latest()
    assert latest["status"] == "complete"
    assert latest["outcome"] == "done"


def test_history_returns_last_n_summaries():
    ts = TraceStore()
    for i in range(3):
        rid = ts.start_run(f"r{i}")
        ts.complete_run(rid, outcome=f"out{i}")
    hist = ts.get_history(n=2)
    assert len(hist) == 2
    assert hist[-1]["outcome"] == "out2"


def test_reset_clears_state():
    ts = TraceStore()
    rid = ts.start_run("a")
    ts.complete_run(rid)
    ts.reset()
    assert ts.get_latest() is None


def test_log_step_with_unknown_run_id_silently_skipped():
    ts = TraceStore()
    ts.start_run("a")
    ts.log_step("run_bogus", "x", "y", {}, {})  # must not raise


def test_trace_latest_endpoint_after_pipeline(client):
    client.post(
        "/pipeline/run",
        json={"source": "social", "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"},
    )
    r = client.get("/trace/latest")
    assert r.status_code == 200
    body = r.json()
    assert len(body["steps"]) >= 4  # ingest+detect+reason+plan+simulate


def test_trace_history_endpoint(client):
    client.post("/pipeline/run", json={"source": "social", "text": "flood G-10"})
    r = client.get("/trace/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
