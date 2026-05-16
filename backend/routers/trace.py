"""Agent Trace endpoints – GET /trace/latest, GET /trace/history

Stub router. Full implementation by Shayan.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.trace_store import trace_store

router = APIRouter(prefix="/trace", tags=["Agent Trace"])


@router.get("/latest", summary="Full agent trace for most recent run")
async def get_latest_trace():
    """Return the complete trace of the most recent pipeline run.

    Each run contains 5 agent steps with input/output data and timing.
    """
    trace = trace_store.get_latest()
    if trace is None:
        raise HTTPException(status_code=404, detail="No pipeline runs recorded yet.")
    return trace


@router.get("/history", summary="Last 10 run summaries")
async def get_trace_history(n: int = 10):
    """Return summaries of the last *n* pipeline runs."""
    return trace_store.get_history(n=n)
