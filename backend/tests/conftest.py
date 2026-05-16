"""Shared pytest fixtures for the CIRO backend test suite.

Adds the backend directory to ``sys.path`` so tests can import
``routers.*``, ``models.*``, and ``services.*`` directly, and exposes a
FastAPI TestClient that is reset between tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Force the Groq integration to remain disabled in tests; we exercise the
# fallback cache path so the suite is hermetic.
os.environ.pop("GROQ_API_KEY", None)


@pytest.fixture
def client():
    """FastAPI TestClient with simulation + trace state reset between tests."""
    from fastapi.testclient import TestClient

    from main import app
    from routers.ingest import _signal_buffer
    from routers.simulate import (
        _default_routes,
        system_state,
    )
    import routers.simulate as simulate_module
    from services.cache import analysis_cache
    from services.trace_store import trace_store

    system_state.traffic_routes = _default_routes()
    system_state.active_tickets.clear()
    system_state.sent_alerts.clear()
    system_state.open_resources.clear()
    simulate_module._last_simulation = None
    _signal_buffer.clear()
    trace_store.reset()
    analysis_cache.clear()

    with TestClient(app) as c:
        yield c
