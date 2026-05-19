"""Simulation Engine – POST /simulate/execute and state management.

Owned by Anas Bin Rashid (Day 3).

Maintains an in-memory ``MockSystemState`` representing the simulated
world (traffic routes, emergency tickets, alerts, resources).  Each
action in an ``ActionPlan`` is executed against this state, and
before/after snapshots are captured for outcome visualisation.

Action handlers:
  - ``reroute_traffic``      – Drop congestion on busiest route
  - ``dispatch_rescue_boats`` – Create a rescue-boat dispatch ticket
  - ``dispatch_traffic_police`` – Create a traffic-police dispatch ticket
  - ``dispatch_ambulance``   – Create an ambulance dispatch ticket
  - ``send_alert``           – Create and record a citizen alert
  - ``open_cooling_centre``  – Register a cooling/relief centre
"""

from __future__ import annotations

import copy
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse

from models.signal import ActionPlan
from models.simulation import Alert, EmergencyTicket, OutcomeSummary, SimulationResult
from services import alert_broadcast
from services.trace_store import trace_store
from utils.logger import log_agent_step

router = APIRouter(prefix="/simulate", tags=["Simulation Engine"])


# ---------------------------------------------------------------------------
# Mock System State
# ---------------------------------------------------------------------------

def _default_routes() -> Dict[str, int]:
    return {
        "G-10 to Blue Area": 85,
        "Shahrah-e-Faisal": 90,
        "Margalla Road": 20,
        "IJP Road": 30,
        "Constitution Avenue": 40,
        "Srinagar Highway": 65,
        "Expressway": 78,
        "GT Road": 55,
    }


@dataclass
class MockSystemState:
    """In-memory representation of the simulated urban system."""
    traffic_routes: Dict[str, int] = field(default_factory=_default_routes)
    active_tickets: List[dict] = field(default_factory=list)
    sent_alerts: List[dict] = field(default_factory=list)
    open_resources: List[str] = field(default_factory=list)

    def snapshot(self) -> dict:
        """Return a JSON-serialisable snapshot of the current state."""
        return {
            "traffic_routes": dict(self.traffic_routes),
            "active_tickets_count": len(self.active_tickets),
            "sent_alerts_count": len(self.sent_alerts),
            "open_resources": list(self.open_resources),
            "avg_congestion": round(
                sum(self.traffic_routes.values()) / max(len(self.traffic_routes), 1), 1
            ),
        }


# Module-level singleton
system_state = MockSystemState()


def _notify_state_change() -> None:
    """Bump SSE / poll version when tickets or alerts change."""
    alert_broadcast.bump()


def _active_trace_run_id() -> str:
    latest = trace_store.get_latest()
    if latest and latest.get("run_id"):
        return latest["run_id"]
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

# Store the most recent simulation for outcome queries
_last_simulation: SimulationResult | None = None


# ---------------------------------------------------------------------------
# Action Handlers
# ---------------------------------------------------------------------------

def _reroute_traffic(state: MockSystemState, params: dict) -> dict:
    """Find the most congested route and drop its congestion to 15."""
    busiest = max(state.traffic_routes, key=state.traffic_routes.get)
    before = state.traffic_routes[busiest]
    state.traffic_routes[busiest] = 15
    return {"route": busiest, "before": before, "after": 15}


def _dispatch_rescue_boats(state: MockSystemState, params: dict) -> dict:
    """Create a rescue-boat dispatch ticket."""
    ticket = {
        "ticket_id": f"tic_{uuid.uuid4().hex[:6]}",
        "crisis_type": params.get("crisis_type", "flood"),
        "location": params.get("target_sector", "G-10"),
        "unit_dispatched": "Rescue Boats",
        "eta_minutes": random.randint(5, 15),
        "status": "dispatched",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    state.active_tickets.append(ticket)
    _notify_state_change()
    return ticket


def _dispatch_traffic_police(state: MockSystemState, params: dict) -> dict:
    """Create a traffic-police dispatch ticket."""
    ticket = {
        "ticket_id": f"tic_{uuid.uuid4().hex[:6]}",
        "crisis_type": params.get("crisis_type", "blockage"),
        "location": params.get("target_sector", "Shahrah-e-Faisal"),
        "unit_dispatched": "Traffic Police",
        "eta_minutes": random.randint(5, 12),
        "status": "dispatched",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    state.active_tickets.append(ticket)
    _notify_state_change()
    return ticket


def _dispatch_ambulance(state: MockSystemState, params: dict) -> dict:
    """Create an ambulance dispatch ticket."""
    ticket = {
        "ticket_id": f"tic_{uuid.uuid4().hex[:6]}",
        "crisis_type": params.get("crisis_type", "accident"),
        "location": params.get("target_sector", "Faizabad"),
        "unit_dispatched": "Rescue 1122",
        "eta_minutes": random.randint(3, 10),
        "status": "dispatched",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    state.active_tickets.append(ticket)
    _notify_state_change()
    return ticket


def _send_alert(state: MockSystemState, params: dict) -> dict:
    """Create and record a citizen alert."""
    alert = {
        "alert_id": f"alr_{uuid.uuid4().hex[:6]}",
        "message": params.get("message", "Emergency alert: please evacuate the area."),
        "target_area": params.get("target_sector", "G-10"),
        "channel": params.get("channel", "push"),
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "recipients_count": random.randint(500, 5000),
    }
    state.sent_alerts.append(alert)
    _notify_state_change()
    return alert


def _open_cooling_centre(state: MockSystemState, params: dict) -> dict:
    """Register a cooling or relief centre as open."""
    sector = params.get("target_sector", "G-9")
    resource_name = f"Cooling Centre {sector}"
    if resource_name not in state.open_resources:
        state.open_resources.append(resource_name)
    return {"resource": resource_name, "status": "opened"}


# Action type → handler mapping
ACTION_HANDLERS = {
    "reroute_traffic": _reroute_traffic,
    "dispatch_rescue_boats": _dispatch_rescue_boats,
    "dispatch_traffic_police": _dispatch_traffic_police,
    "dispatch_ambulance": _dispatch_ambulance,
    "send_alert": _send_alert,
    "send_flood_alert": _send_alert,
    "send_heat_advisory": _send_alert,
    "open_cooling_centre": _open_cooling_centre,
    "open_cooling_centres": _open_cooling_centre,
    "open_relief_camp": _open_cooling_centre,
    "restrict_outdoor_activity": _send_alert,
    "update_navigation_apps": _send_alert,
    "close_road_segment": _reroute_traffic,
    "dispatch_fire_brigade": _dispatch_ambulance,
}


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.post("/execute", response_model=SimulationResult, summary="Execute simulation")
async def execute_simulation(plan: ActionPlan):
    """Execute all actions in an ActionPlan against the mock system state.

    Captures before/after snapshots and computes outcome metrics.
    """
    global _last_simulation
    start = time.time()

    # Snapshot BEFORE
    state_before = system_state.snapshot()

    # Execute each action
    actions_executed = []
    tickets_created = []
    alerts_sent = []
    routes_updated = []

    for action in plan.actions:
        handler = ACTION_HANDLERS.get(action.type)
        if handler is None:
            continue  # Unknown action type – skip

        result = handler(system_state, action.params)
        actions_executed.append(action.type)

        # Categorise the result
        if "ticket_id" in result:
            tickets_created.append(EmergencyTicket(**result))
        elif "alert_id" in result:
            alerts_sent.append(Alert(**result))
        elif "route" in result:
            routes_updated.append(result)
        elif "resource" in result:
            pass  # Resource opening is tracked in state

    # Snapshot AFTER
    state_after = system_state.snapshot()

    # Compute congestion reduction
    avg_before = state_before.get("avg_congestion", 0)
    avg_after = state_after.get("avg_congestion", 0)
    congestion_reduction = round(
        ((avg_before - avg_after) / avg_before * 100) if avg_before > 0 else 0, 1
    )

    # Min ETA from tickets
    etas = [t.eta_minutes for t in tickets_created]
    min_eta = min(etas) if etas else 0

    sim_run_id = f"sim_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    trace_run_id = _active_trace_run_id()
    elapsed_ms = int((time.time() - start) * 1000)

    simulation_result = SimulationResult(
        run_id=sim_run_id,
        actions_executed=actions_executed,
        tickets_created=tickets_created,
        alerts_sent=alerts_sent,
        routes_updated=routes_updated,
        state_before=state_before,
        state_after=state_after,
        estimated_congestion_reduction=congestion_reduction,
        estimated_response_time_minutes=min_eta,
    )

    _last_simulation = simulation_result
    _notify_state_change()

    # Log the trace step (same run_id as ingest/detect/reason/plan)
    trace_store.log_step(
        run_id=trace_run_id,
        agent="simulation-agent",
        step="execute_actions",
        input_data=plan.model_dump(mode="json"),
        output_data={
            "actions_executed": actions_executed,
            "tickets": len(tickets_created),
            "alerts": len(alerts_sent),
            "congestion_reduction": congestion_reduction,
        },
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="simulation-agent",
        step="execute_actions",
        input_data={"plan_id": plan.plan_id},
        output_data={"actions": len(actions_executed), "congestion_reduction": congestion_reduction},
        duration_ms=elapsed_ms,
    )

    return simulation_result


@router.get("/state", summary="Current mock system state")
async def get_state():
    """Return the current mock system state."""
    return system_state.snapshot()


@router.post("/reset", summary="Reset all mock state to defaults")
async def reset_state():
    """Reset the mock system state to clean defaults for demo resets."""
    global _last_simulation
    system_state.traffic_routes = _default_routes()
    system_state.active_tickets.clear()
    system_state.sent_alerts.clear()
    system_state.open_resources.clear()
    _last_simulation = None
    trace_store.reset()
    alert_broadcast.reset()
    return {"status": "reset", "message": "All state reset to defaults"}


@router.get("/tickets", summary="List all emergency tickets")
async def get_tickets():
    """Return all emergency tickets from the current state."""
    return system_state.active_tickets


@router.get("/alerts", summary="List all sent alerts")
async def get_alerts():
    """Return all sent alerts from the current state."""
    return system_state.sent_alerts


@router.get("/alerts/version", summary="Alert/ticket snapshot version for polling")
async def alerts_version():
    """Lightweight poll target — clients compare ``version`` to detect new alerts."""
    return alert_broadcast.snapshot(
        system_state.sent_alerts,
        system_state.active_tickets,
    )


@router.get("/alerts/stream", summary="Server-Sent Events stream for alerts and tickets")
async def alerts_stream(once: bool = False):
    """Push alert/ticket updates to web and mobile clients in near real time."""

    async def _generator():
        async for chunk in alert_broadcast.event_stream(
            lambda: list(system_state.sent_alerts),
            lambda: list(system_state.active_tickets),
            poll_interval=1.0,
            max_events=1 if once else None,
        ):
            yield chunk

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.patch("/tickets/{ticket_id}/status", summary="Update ticket status")
async def update_ticket_status(
    ticket_id: str,
    status: str = "resolved",
    body: dict | None = Body(default=None),
):
    """Update the status of a specific emergency ticket."""
    if body and isinstance(body, dict) and body.get("status"):
        status = str(body["status"])
    for ticket in system_state.active_tickets:
        if ticket["ticket_id"] == ticket_id:
            ticket["status"] = status
            _notify_state_change()
            return {"ticket_id": ticket_id, "new_status": status}
    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")


def get_last_simulation() -> SimulationResult | None:
    """Return the most recent simulation result (used by outcome router)."""
    return _last_simulation
