"""End-to-end pipeline endpoint – POST /pipeline/run

Single-call orchestration that chains every agent in CIRO's reasoning
pipeline.  Used by the web dashboard's "Trigger Pipeline" button, the
Flutter app's FAB, and the scenario runner.

Flow:
    RawSignalInput
        -> Signal Ingestion       (normalise + buffer)
        -> Event Detection        (classify + score)
        -> Reasoning & Analysis   (impact + summary)
        -> Action Planning        (response actions)
        -> Simulation Engine      (execute + before/after)

The endpoint reuses the existing per-agent handlers so behavior stays
identical to calling each endpoint individually.  Trace logging is
preserved end-to-end and the run is marked complete at the end.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from models.signal import (
    ActionPlan,
    CrisisAnalysis,
    CrisisEvent,
    RawSignalInput,
    SignalBatch,
)
from models.simulation import SimulationResult
from routers import detect as detect_router
from routers import ingest as ingest_router
from routers import plan as plan_router
from routers import reason as reason_router
from routers import simulate as simulate_router
from services.trace_store import trace_store

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


class PipelineResult(BaseModel):
    """Combined output of the full 5-agent pipeline."""
    run_id: str
    batch: SignalBatch
    event: CrisisEvent
    analysis: CrisisAnalysis
    plan: ActionPlan
    simulation: SimulationResult
    total_duration_ms: int = 0


@router.post("/run", response_model=PipelineResult, summary="Run the full 5-agent pipeline end-to-end")
async def run_pipeline(raw: RawSignalInput):
    """Execute the complete CIRO pipeline against a single raw signal.

    Returns one ``PipelineResult`` containing every intermediate output
    plus the trace ``run_id``.  Trace logging happens at each stage so
    ``GET /trace/latest`` will show all five steps after this returns.
    """
    # 1. Ingestion
    batch: SignalBatch = await ingest_router.ingest_signal(raw)

    # 2. Detection
    event: CrisisEvent = await detect_router.detect_crisis(batch)

    # 3. Reasoning
    analysis: CrisisAnalysis = await reason_router.analyse_crisis(event)

    # 4. Planning
    plan_request = plan_router.PlanRequest(
        **event.model_dump(),
        analysis=analysis,
    )
    action_plan: ActionPlan = await plan_router.generate_action_plan(plan_request)

    # 5. Simulation
    simulation: SimulationResult = await simulate_router.execute_simulation(action_plan)

    # Complete the trace run
    latest = trace_store.get_latest()
    run_id = latest["run_id"] if latest else "unknown"
    total_duration = latest.get("total_duration_ms", 0) if latest else 0
    trace_store.complete_run(
        run_id=run_id,
        outcome=f"{event.crisis_type.value.upper()} at {event.location} – {len(action_plan.actions)} actions executed",
    )

    return PipelineResult(
        run_id=run_id,
        batch=batch,
        event=event,
        analysis=analysis,
        plan=action_plan,
        simulation=simulation,
        total_duration_ms=total_duration,
    )
