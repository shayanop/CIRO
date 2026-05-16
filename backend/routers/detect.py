"""Event Detection Agent – POST /detect/crisis

Stub router. Full implementation by Hasnain.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from models.signal import CrisisEvent, CrisisType, Severity, SignalBatch
from services.trace_store import trace_store
from utils.logger import log_agent_step

router = APIRouter(prefix="/detect", tags=["Event Detection"])


# ---------------------------------------------------------------------------
# Confidence Scoring Algorithm
# ---------------------------------------------------------------------------

def compute_confidence(signals: list, crisis_type: str) -> float:
    """Compute detection confidence from signal evidence."""
    score = 0.0

    # Base score from signal count
    if len(signals) >= 3:
        score += 0.30
    elif len(signals) == 2:
        score += 0.15
    else:
        score += 0.05

    # Multi-source bonus
    sources = {s.get("source", s.source if hasattr(s, "source") else "unknown") for s in signals}
    if len(sources) >= 3:
        score += 0.40
    elif len(sources) >= 2:
        score += 0.25

    # Severity boost
    for s in signals:
        hint = s.get("severity_hint", getattr(s, "severity_hint", None))
        if hint == "high":
            score += 0.30
            break
        elif hint == "medium":
            score += 0.15
            break

    return min(round(score, 2), 1.0)


def confidence_to_severity(confidence: float) -> Severity:
    """Map confidence score to severity level."""
    if confidence >= 0.8:
        return Severity.CRITICAL
    elif confidence >= 0.6:
        return Severity.HIGH
    elif confidence >= 0.4:
        return Severity.MEDIUM
    return Severity.LOW


# ---------------------------------------------------------------------------
# Crisis Type Detection
# ---------------------------------------------------------------------------

FLOOD_KEYWORDS = {"flood", "flash flood", "pani", "bhar", "doob", "waterlogging", "nala", "ubhal", "baarish", "rain"}
HEATWAVE_KEYWORDS = {"heatwave", "heat", "garmi", "degrees", "collapsing", "behosh", "temperature"}
BLOCKAGE_KEYWORDS = {"blocked", "jam", "jammed", "blockage", "congestion", "protest"}
ACCIDENT_KEYWORDS = {"accident", "hadsa", "crash", "collision", "fire"}


def detect_crisis_type(signals) -> CrisisType:
    """Determine the crisis type from signal keywords."""
    scores = {
        CrisisType.FLOOD: 0,
        CrisisType.HEATWAVE: 0,
        CrisisType.BLOCKAGE: 0,
        CrisisType.ACCIDENT: 0,
    }
    for s in signals:
        keywords = getattr(s, "keywords", []) or s.get("keywords", []) if isinstance(s, dict) else s.keywords
        text = (getattr(s, "content", "") or (s.get("content", "") if isinstance(s, dict) else "")).lower()
        combined = " ".join(keywords) + " " + text

        for kw in FLOOD_KEYWORDS:
            if kw in combined:
                scores[CrisisType.FLOOD] += 1
        for kw in HEATWAVE_KEYWORDS:
            if kw in combined:
                scores[CrisisType.HEATWAVE] += 1
        for kw in BLOCKAGE_KEYWORDS:
            if kw in combined:
                scores[CrisisType.BLOCKAGE] += 1
        for kw in ACCIDENT_KEYWORDS:
            if kw in combined:
                scores[CrisisType.ACCIDENT] += 1

    return max(scores, key=scores.get)


@router.post("/crisis", response_model=CrisisEvent, summary="Detect crisis from signal batch")
async def detect_crisis(batch: SignalBatch):
    """Detect a crisis event from a SignalBatch using keyword clustering,
    cross-source corroboration, and confidence scoring."""
    start = time.time()

    crisis_type = detect_crisis_type(batch.signals)
    confidence = compute_confidence(batch.signals, crisis_type.value)
    severity = confidence_to_severity(confidence)

    location = batch.primary_location or (
        batch.signals[0].location if batch.signals else "Unknown"
    )

    event = CrisisEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        crisis_type=crisis_type,
        location=location or "Unknown",
        confidence=confidence,
        severity=severity,
        signals=batch.signals,
        explanation=f"{crisis_type.value.upper()} detected at {location} with {confidence:.0%} confidence from {len(batch.signals)} signal(s).",
        detected_at=datetime.now(timezone.utc),
    )

    elapsed_ms = int((time.time() - start) * 1000)

    # Log trace step
    latest = trace_store.get_latest()
    run_id = latest["run_id"] if latest and latest.get("status") == "running" else "unknown"
    trace_store.log_step(
        run_id=run_id,
        agent="event-detection-agent",
        step="detect_crisis",
        input_data={"batch_id": batch.batch_id, "signal_count": len(batch.signals)},
        output_data=event.model_dump(mode="json"),
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="event-detection-agent",
        step="detect_crisis",
        input_data={"batch_id": batch.batch_id},
        output_data={"event_id": event.event_id, "crisis_type": event.crisis_type.value, "confidence": event.confidence},
        duration_ms=elapsed_ms,
    )

    return event
