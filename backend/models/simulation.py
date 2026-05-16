"""Pydantic models for the simulation layer.

Covers emergency tickets, alerts, simulation results, outcome summaries,
and the in-memory mock world state shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EmergencyTicket(BaseModel):
    """A dispatch ticket created by the simulation engine."""
    ticket_id: str
    crisis_type: str
    location: str
    unit_dispatched: str  # "Rescue Boats" | "Traffic Police" | "Rescue 1122" | ...
    eta_minutes: int
    status: str = "open"  # open | dispatched | resolved
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    """A simulated alert/notification dispatched to citizens."""
    alert_id: str
    message: str
    target_area: str
    channel: str = "push"  # push | sms | broadcast
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recipients_count: int = 0


class SimulationResult(BaseModel):
    """Full output of a simulation run."""
    run_id: str
    actions_executed: List[str] = Field(default_factory=list)
    tickets_created: List[EmergencyTicket] = Field(default_factory=list)
    alerts_sent: List[Alert] = Field(default_factory=list)
    routes_updated: List[dict] = Field(default_factory=list)
    state_before: dict = Field(default_factory=dict)
    state_after: dict = Field(default_factory=dict)
    estimated_congestion_reduction: float = 0.0
    estimated_response_time_minutes: int = 0


class OutcomeSummary(BaseModel):
    """Aggregated outcome metrics shown on the command dashboard."""
    congestion_reduction_pct: float = 0.0
    vehicles_rerouted: int = 0
    min_eta_minutes: int = 0
    alerts_dispatched: int = 0
    tickets_created: int = 0
    resources_opened: List[str] = Field(default_factory=list)
    state_before: Optional[dict] = None
    state_after: Optional[dict] = None
