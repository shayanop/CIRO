"""Action Planning Agent – POST /plan/actions

Stub router. Full implementation by Saad.
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter

from models.signal import Action, ActionPlan, CrisisAnalysis, CrisisEvent, Severity
from services.trace_store import trace_store
from utils.logger import log_agent_step

router = APIRouter(prefix="/plan", tags=["Action Planning"])

# ---------------------------------------------------------------------------
# Action generation rules: (crisis_type, severity) → list of action types
# ---------------------------------------------------------------------------

ACTION_RULES = {
    ("flood", "high"): [
        ("reroute_traffic", 1),
        ("dispatch_rescue_boats", 2),
        ("send_flood_alert", 3),
        ("open_relief_camp", 4),
    ],
    ("flood", "critical"): [
        ("reroute_traffic", 1),
        ("dispatch_rescue_boats", 2),
        ("send_flood_alert", 3),
        ("open_relief_camp", 4),
    ],
    ("flood", "medium"): [
        ("send_flood_alert", 1),
        ("reroute_traffic", 2),
    ],
    ("flood", "low"): [],
    ("heatwave", "high"): [
        ("send_heat_advisory", 1),
        ("open_cooling_centres", 2),
        ("dispatch_ambulance", 3),
        ("restrict_outdoor_activity", 4),
    ],
    ("heatwave", "critical"): [
        ("send_heat_advisory", 1),
        ("open_cooling_centres", 2),
        ("dispatch_ambulance", 3),
        ("restrict_outdoor_activity", 4),
    ],
    ("heatwave", "medium"): [
        ("send_heat_advisory", 1),
        ("open_cooling_centres", 2),
    ],
    ("heatwave", "low"): [],
    ("blockage", "high"): [
        ("reroute_traffic", 1),
        ("dispatch_traffic_police", 2),
        ("update_navigation_apps", 3),
    ],
    ("blockage", "medium"): [
        ("reroute_traffic", 1),
        ("dispatch_traffic_police", 2),
        ("update_navigation_apps", 3),
    ],
    ("blockage", "critical"): [
        ("reroute_traffic", 1),
        ("dispatch_traffic_police", 2),
        ("update_navigation_apps", 3),
    ],
    ("blockage", "low"): [],
    ("accident", "high"): [
        ("dispatch_ambulance", 1),
        ("dispatch_fire_brigade", 2),
        ("close_road_segment", 3),
    ],
    ("accident", "critical"): [
        ("dispatch_ambulance", 1),
        ("dispatch_fire_brigade", 2),
        ("close_road_segment", 3),
    ],
    ("accident", "medium"): [
        ("dispatch_traffic_police", 1),
    ],
    ("accident", "low"): [],
    # Fire
    ("fire", "high"): [
        ("dispatch_fire_brigade", 1),
        ("dispatch_ambulance", 2),
        ("close_road_segment", 3),
        ("send_alert", 4),
    ],
    ("fire", "critical"): [
        ("dispatch_fire_brigade", 1),
        ("dispatch_ambulance", 2),
        ("close_road_segment", 3),
        ("send_alert", 4),
        ("open_relief_camp", 5),
    ],
    ("fire", "medium"): [
        ("dispatch_fire_brigade", 1),
        ("send_alert", 2),
    ],
    ("fire", "low"): [
        ("send_alert", 1),
    ],
    # Earthquake
    ("earthquake", "high"): [
        ("dispatch_rescue_boats", 1),
        ("dispatch_ambulance", 2),
        ("open_relief_camp", 3),
        ("send_alert", 4),
    ],
    ("earthquake", "critical"): [
        ("dispatch_rescue_boats", 1),
        ("dispatch_ambulance", 2),
        ("dispatch_fire_brigade", 3),
        ("open_relief_camp", 4),
        ("send_alert", 5),
    ],
    ("earthquake", "medium"): [
        ("send_alert", 1),
        ("dispatch_traffic_police", 2),
    ],
    ("earthquake", "low"): [],
    # Storm / cyclone / landslide
    ("storm", "high"): [
        ("send_alert", 1),
        ("close_road_segment", 2),
        ("open_relief_camp", 3),
        ("reroute_traffic", 4),
    ],
    ("storm", "critical"): [
        ("send_alert", 1),
        ("close_road_segment", 2),
        ("open_relief_camp", 3),
        ("reroute_traffic", 4),
        ("dispatch_rescue_boats", 5),
    ],
    ("storm", "medium"): [
        ("send_alert", 1),
        ("restrict_outdoor_activity", 2),
    ],
    ("storm", "low"): [],
    # Infrastructure (power outage, gas leak, collapse, sinkhole)
    ("infrastructure", "high"): [
        ("dispatch_ambulance", 1),
        ("close_road_segment", 2),
        ("send_alert", 3),
    ],
    ("infrastructure", "critical"): [
        ("dispatch_ambulance", 1),
        ("dispatch_fire_brigade", 2),
        ("close_road_segment", 3),
        ("send_alert", 4),
        ("open_relief_camp", 5),
    ],
    ("infrastructure", "medium"): [
        ("dispatch_traffic_police", 1),
        ("send_alert", 2),
    ],
    ("infrastructure", "low"): [],
}


class PlanRequest(CrisisEvent):
    """Accepts a CrisisEvent (optionally with analysis) for action planning."""
    analysis: CrisisAnalysis | None = None


@router.post("/actions", response_model=ActionPlan, summary="Generate action plan")
async def generate_action_plan(event: PlanRequest):
    """Generate a coordinated response plan based on crisis type and severity.

    The plan is built from a 2-D lookup table keyed by
    ``(crisis_type, severity)``.  Parameters are resolved from the event.
    """
    start = time.time()

    key = (event.crisis_type.value.lower(), event.severity.value.lower())
    action_templates = ACTION_RULES.get(key, [])

    actions = []
    for action_type, priority in action_templates:
        actions.append(
            Action(
                action_id=f"act_{uuid.uuid4().hex[:6]}",
                type=action_type,
                params={
                    "target_sector": event.location,
                    "crisis_type": event.crisis_type.value,
                },
                priority=priority,
            )
        )

    plan = ActionPlan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        event_id=event.event_id,
        actions=actions,
    )

    elapsed_ms = int((time.time() - start) * 1000)

    # Log trace step
    latest = trace_store.get_latest()
    run_id = latest["run_id"] if latest and latest.get("status") == "running" else "unknown"
    trace_store.log_step(
        run_id=run_id,
        agent="action-planning-agent",
        step="generate_plan",
        input_data={"event_id": event.event_id, "crisis_type": event.crisis_type.value, "severity": event.severity.value},
        output_data=plan.model_dump(mode="json"),
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="action-planning-agent",
        step="generate_plan",
        input_data={"event_id": event.event_id},
        output_data={"plan_id": plan.plan_id, "action_count": len(plan.actions)},
        duration_ms=elapsed_ms,
    )

    return plan
