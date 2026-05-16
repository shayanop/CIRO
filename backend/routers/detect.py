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

def _attr(signal, name, default=None):
    """Fetch a field from either a Pydantic model or a dict."""
    if isinstance(signal, dict):
        return signal.get(name, default)
    return getattr(signal, name, default)


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
    sources = {_attr(s, "source", "unknown") for s in signals}
    if len(sources) >= 3:
        score += 0.40
    elif len(sources) >= 2:
        score += 0.25

    # Severity boost (use highest-severity signal in the batch)
    for s in signals:
        hint = _attr(s, "severity_hint")
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

FLOOD_KEYWORDS = {"flood", "flash flood", "pani", "bhar", "doob", "submerged", "waterlogging", "waterlogged", "nala", "ubhal", "baarish", "rain", "river", "overflow", "darya"}
HEATWAVE_KEYWORDS = {"heatwave", "heat", "heatstroke", "garmi", "degrees", "collapsing", "behosh", "temperature", "cooling"}
BLOCKAGE_KEYWORDS = {"blocked", "jam", "jammed", "blockage", "congestion", "protest", "riot", "stranded", "diverted", "ehtjaj"}
ACCIDENT_KEYWORDS = {"accident", "hadsa", "crash", "collision", "tasadum", "pile-up", "overturned", "derailed", "zakhmi", "injured"}
FIRE_KEYWORDS = {"fire", "aag", "burning", "smoke", "flames", "cylinder blast", "blaze"}
EARTHQUAKE_KEYWORDS = {"earthquake", "zalzala", "tremors", "jhatke", "magnitude"}
STORM_KEYWORDS = {"cyclone", "tornado", "landslide", "hailstorm", "windstorm", "dust storm", "snowfall", "toofan"}
INFRA_KEYWORDS = {"collapse", "collapsed", "sinkhole", "chhat gir", "power line", "bijli", "khamba", "sparks", "outage", "blackout", "leak", "leakage", "sewerage", "transformer", "dhamaka", "blast", "explosion"}


def detect_crisis_type(signals) -> CrisisType:
    """Determine the crisis type from signal keywords across all signals."""
    scores = {
        CrisisType.FLOOD: 0,
        CrisisType.HEATWAVE: 0,
        CrisisType.BLOCKAGE: 0,
        CrisisType.ACCIDENT: 0,
        CrisisType.FIRE: 0,
        CrisisType.EARTHQUAKE: 0,
        CrisisType.STORM: 0,
        CrisisType.INFRASTRUCTURE: 0,
    }
    keyword_buckets = {
        CrisisType.FLOOD: FLOOD_KEYWORDS,
        CrisisType.HEATWAVE: HEATWAVE_KEYWORDS,
        CrisisType.BLOCKAGE: BLOCKAGE_KEYWORDS,
        CrisisType.ACCIDENT: ACCIDENT_KEYWORDS,
        CrisisType.FIRE: FIRE_KEYWORDS,
        CrisisType.EARTHQUAKE: EARTHQUAKE_KEYWORDS,
        CrisisType.STORM: STORM_KEYWORDS,
        CrisisType.INFRASTRUCTURE: INFRA_KEYWORDS,
    }
    for s in signals:
        keywords = _attr(s, "keywords", []) or []
        text = (_attr(s, "content", "") or "").lower()
        combined = " ".join(keywords) + " " + text

        for ctype, bucket in keyword_buckets.items():
            for kw in bucket:
                if kw in combined:
                    scores[ctype] += 1

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
