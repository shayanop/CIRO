"""Outcome Visualisation – GET /outcome/summary

Owned by Anas Bin Rashid (Day 4).

Computes aggregated outcome metrics by comparing the before/after state
from the most recent simulation run.  These metrics power the Flutter
command dashboard's before/after view.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.simulation import OutcomeSummary

router = APIRouter(prefix="/outcome", tags=["Outcome"])


@router.get("/summary", response_model=OutcomeSummary, summary="Before/after outcome metrics")
async def get_outcome_summary():
    """Return aggregated outcome metrics from the most recent simulation.

    Computes:
    - ``congestion_reduction_pct`` — percentage drop in average congestion
    - ``vehicles_rerouted`` — estimated vehicles rerouted (200–800 based on congestion)
    - ``min_eta_minutes`` — shortest dispatch ETA from created tickets
    - ``alerts_dispatched`` — total alert recipients across all alerts
    - ``tickets_created`` — number of emergency tickets created
    - ``resources_opened`` — list of opened relief/cooling centres
    """
    # Import here to avoid circular import
    from routers.simulate import get_last_simulation, system_state

    sim = get_last_simulation()
    if sim is None:
        raise HTTPException(
            status_code=404,
            detail="No simulation has been run yet. Call POST /simulate/execute first.",
        )

    # Congestion reduction
    avg_before = sim.state_before.get("avg_congestion", 0)
    avg_after = sim.state_after.get("avg_congestion", 0)
    congestion_pct = round(
        ((avg_before - avg_after) / avg_before * 100) if avg_before > 0 else 0, 1
    )

    # Vehicles rerouted (simulated: scale by congestion difference)
    congestion_delta = max(avg_before - avg_after, 0)
    vehicles = int(congestion_delta * 12)  # ~12 vehicles per congestion point
    vehicles = max(200, min(vehicles, 800)) if congestion_delta > 0 else 0

    # Min ETA from tickets
    etas = [t.eta_minutes for t in sim.tickets_created]
    min_eta = min(etas) if etas else 0

    # Total alert recipients
    total_recipients = sum(a.recipients_count for a in sim.alerts_sent)

    return OutcomeSummary(
        congestion_reduction_pct=congestion_pct,
        vehicles_rerouted=vehicles,
        min_eta_minutes=min_eta,
        alerts_dispatched=total_recipients,
        tickets_created=len(sim.tickets_created),
        resources_opened=list(system_state.open_resources),
        state_before=sim.state_before,
        state_after=sim.state_after,
    )
