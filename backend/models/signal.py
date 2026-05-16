"""Pydantic models for signal ingestion and event detection.

Defines the canonical data shapes that flow through the first three agents
in the CIRO pipeline: Signal → SignalBatch → CrisisEvent → CrisisAnalysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CrisisType(str, Enum):
    """Recognised crisis categories."""
    FLOOD = "flood"
    HEATWAVE = "heatwave"
    BLOCKAGE = "blockage"
    ACCIDENT = "accident"
    INFRASTRUCTURE = "infrastructure"


class Severity(str, Enum):
    """Four-level severity ladder."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Signal models
# ---------------------------------------------------------------------------

class RawSignalInput(BaseModel):
    """Raw payload accepted by POST /ingest/signal."""
    source: str = Field(..., description="social | weather | traffic")
    text: str = Field(..., description="Free-form text (Urdu or English)")
    metadata: Optional[dict] = Field(default=None, description="Optional geo/user metadata")


class Signal(BaseModel):
    """A normalised signal after ingestion processing."""
    signal_id: str
    source: str
    content: str
    location: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: Optional[str] = "en"
    severity_hint: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class SignalBatch(BaseModel):
    """Collection of normalised signals passed to the Event Detection Agent."""
    batch_id: str
    signals: List[Signal]
    primary_location: Optional[str] = None


# ---------------------------------------------------------------------------
# Event Detection models
# ---------------------------------------------------------------------------

class CrisisEvent(BaseModel):
    """Output of the Event Detection Agent."""
    event_id: str
    crisis_type: CrisisType
    location: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: Severity
    signals: List[Signal] = Field(default_factory=list)
    explanation: str = ""
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Reasoning / Analysis models
# ---------------------------------------------------------------------------

class CrisisAnalysis(BaseModel):
    """Output of the Reasoning & Analysis Agent (Gemini-powered)."""
    analysis_id: str
    event_id: str
    impact: List[str] = Field(default_factory=list, description="Impact bullet points")
    affected_population: int = 0
    infrastructure_at_risk: List[str] = Field(default_factory=list)
    urgency: str = "monitoring"  # immediate | within_hour | monitoring
    summary: str = ""


# ---------------------------------------------------------------------------
# Action Planning models
# ---------------------------------------------------------------------------

class Action(BaseModel):
    """A single executable action within a plan."""
    action_id: str
    type: str  # e.g. reroute_traffic, dispatch_rescue_boats
    params: dict = Field(default_factory=dict)
    priority: int = 1


class ActionPlan(BaseModel):
    """Output of the Action Planning Agent."""
    plan_id: str
    event_id: str
    actions: List[Action] = Field(default_factory=list)
