"""Event Detection Agent – POST /detect/crisis

Stub router. Full implementation by Hasnain.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Tuple

from fastapi import APIRouter

from models.signal import CrisisEvent, CrisisType, Severity, SignalBatch
from services.trace_store import trace_store
from utils.logger import log_agent_step

router = APIRouter(prefix="/detect", tags=["Event Detection"])


# ---------------------------------------------------------------------------
# Corroboration data loading (cached)
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def _load_weather_alerts() -> list:
    try:
        data = json.loads((_DATA_DIR / "weather_mock.json").read_text(encoding="utf-8"))
        return data.get("alerts", []) or []
    except Exception:
        return []


@lru_cache(maxsize=1)
def _load_traffic_routes() -> list:
    try:
        data = json.loads((_DATA_DIR / "traffic_mock.json").read_text(encoding="utf-8"))
        return data.get("routes", []) or []
    except Exception:
        return []


# Maps a weather alert event keyword to the crisis_type it corroborates
_WEATHER_EVENT_TO_TYPE = {
    "rain": "flood",
    "flood": "flood",
    "flash flood": "flood",
    "heat": "heatwave",
    "heatwave": "heatwave",
    "cyclone": "storm",
    "storm": "storm",
    "landslide": "storm",
    "snow": "storm",
    "smog": "infrastructure",
    "earthquake": "earthquake",
    "fire": "fire",
}


def _signal_locations(signals) -> list[str]:
    return [
        (_attr(s, "location") or "").strip()
        for s in signals
        if _attr(s, "location")
    ]


def _engagement_bonus(signals) -> float:
    """Bonus based on the single most-engaged signal."""
    best = 0
    for s in signals:
        eng = _attr(s, "engagement")
        if eng is None:
            meta = _attr(s, "metadata", {}) or {}
            if isinstance(meta, dict):
                eng = meta.get("engagement") or meta.get("engagement_count") or 0
        try:
            eng = int(eng or 0)
        except (TypeError, ValueError):
            eng = 0
        best = max(best, eng)
    if best > 5000:
        return 0.15
    if best > 2000:
        return 0.10
    if best > 500:
        return 0.05
    return 0.0


def _weather_corroboration_bonus(signals, crisis_type: str) -> Tuple[float, list[str]]:
    """+0.15 if a weather alert region matches a signal location AND its event
    aligns with the crisis type. Returns (bonus, matched_alert_ids)."""
    locs = [loc.lower() for loc in _signal_locations(signals)]
    if not locs:
        return 0.0, []
    matched = []
    for alert in _load_weather_alerts():
        regions = [str(r).lower() for r in alert.get("regions", [])]
        description = str(alert.get("description", "")).lower()
        event = str(alert.get("event", "")).lower()
        expected_type = next(
            (v for k, v in _WEATHER_EVENT_TO_TYPE.items() if k in event),
            None,
        )
        if expected_type != crisis_type:
            continue
        for loc in locs:
            if not loc:
                continue
            if any(loc in region or region in loc for region in regions):
                matched.append(alert.get("alert_id", ""))
                break
            if loc in description:
                matched.append(alert.get("alert_id", ""))
                break
    if matched:
        return 0.15, matched
    return 0.0, []


def _traffic_corroboration_bonus(signals) -> Tuple[float, list[str]]:
    """+0.15 if a signal location matches a route with status=blocked."""
    locs = [loc.lower() for loc in _signal_locations(signals)]
    if not locs:
        return 0.0, []
    matched = []
    for route in _load_traffic_routes():
        if str(route.get("status", "")).lower() != "blocked":
            continue
        name = str(route.get("name", "")).lower()
        city = str(route.get("city", "")).lower()
        for loc in locs:
            if not loc:
                continue
            if loc in name or name in loc or loc in city:
                matched.append(route.get("route_id", ""))
                break
    if matched:
        return 0.15, matched
    return 0.0, []


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
    score, _ = compute_confidence_detailed(signals, crisis_type)
    return score


def compute_confidence_detailed(
    signals: list, crisis_type: str
) -> Tuple[float, dict]:
    """Return (confidence, breakdown) so callers can show why we scored it."""
    score = 0.0
    breakdown: dict = {}

    # Base score from signal count
    if len(signals) >= 3:
        score += 0.30
        breakdown["signal_count_bonus"] = 0.30
    elif len(signals) == 2:
        score += 0.15
        breakdown["signal_count_bonus"] = 0.15
    else:
        score += 0.05
        breakdown["signal_count_bonus"] = 0.05

    # Multi-source bonus
    sources = {_attr(s, "source", "unknown") for s in signals}
    if len(sources) >= 3:
        score += 0.40
        breakdown["source_diversity_bonus"] = 0.40
    elif len(sources) >= 2:
        score += 0.25
        breakdown["source_diversity_bonus"] = 0.25
    else:
        breakdown["source_diversity_bonus"] = 0.0

    # Severity boost (use highest-severity signal in the batch)
    severity_bonus = 0.0
    for s in signals:
        hint = _attr(s, "severity_hint")
        if hint == "high":
            severity_bonus = 0.30
            break
        if hint == "medium":
            severity_bonus = 0.15
            break
    score += severity_bonus
    breakdown["severity_bonus"] = severity_bonus

    # Engagement bonus
    eng_bonus = _engagement_bonus(signals)
    score += eng_bonus
    breakdown["engagement_bonus"] = eng_bonus

    # Weather corroboration
    weather_bonus, weather_matches = _weather_corroboration_bonus(signals, crisis_type)
    score += weather_bonus
    breakdown["weather_corroboration_bonus"] = weather_bonus
    breakdown["weather_matches"] = weather_matches

    # Traffic corroboration
    traffic_bonus, traffic_matches = _traffic_corroboration_bonus(signals)
    score += traffic_bonus
    breakdown["traffic_corroboration_bonus"] = traffic_bonus
    breakdown["traffic_matches"] = traffic_matches

    # Strong keyword evidence on the highest-severity signal in the batch
    strong_bonus = 0.0
    for s in signals:
        hint = _attr(s, "severity_hint")
        kws = _attr(s, "keywords", []) or []
        if hint == "high" and len(kws) >= 2:
            strong_bonus = 0.20
            break
        if hint == "medium" and len(kws) >= 2:
            strong_bonus = max(strong_bonus, 0.10)
    score += strong_bonus
    breakdown["strong_evidence_bonus"] = strong_bonus

    # Resolved location on any signal (urban crises are geo-specific)
    if any(_attr(s, "location") for s in signals):
        score += 0.15
        breakdown["location_anchor_bonus"] = 0.15
    else:
        breakdown["location_anchor_bonus"] = 0.0

    return min(round(score, 2), 1.0), breakdown


def confidence_to_severity(confidence: float) -> Severity:
    """Map confidence score to severity level."""
    if confidence >= 0.75:
        return Severity.CRITICAL
    elif confidence >= 0.55:
        return Severity.HIGH
    elif confidence >= 0.35:
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


_SEVERITY_LADDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


def _bump_severity(s: Severity) -> Severity:
    idx = _SEVERITY_LADDER.index(s)
    return _SEVERITY_LADDER[min(idx + 1, len(_SEVERITY_LADDER) - 1)]


def _recent_event_signature_count(
    location: str, crisis_type: str, window_minutes: int = 5
) -> int:
    """Count how many detect_crisis steps in the last N minutes had the same
    location+crisis_type signature. Reads from trace_store history."""
    if not location or not crisis_type:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    count = 0
    runs = list(getattr(trace_store, "_runs", []))
    current = getattr(trace_store, "_current_run", None)
    if current is not None:
        runs = runs + [current]
    for run in runs:
        for step in run.get("steps", []):
            if step.get("agent") != "event-detection-agent":
                continue
            out = step.get("output") or {}
            if not isinstance(out, dict):
                continue
            if out.get("crisis_type") != crisis_type:
                continue
            if (out.get("location") or "").lower() != location.lower():
                continue
            ts_raw = step.get("timestamp")
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                count += 1
    return count


@router.post("/crisis", response_model=CrisisEvent, summary="Detect crisis from signal batch")
async def detect_crisis(batch: SignalBatch):
    """Detect a crisis event from a SignalBatch using keyword clustering,
    cross-source corroboration, confidence scoring, and severity escalation
    when the same location+type recurs within 5 minutes."""
    start = time.time()

    crisis_type = detect_crisis_type(batch.signals)
    confidence, breakdown = compute_confidence_detailed(batch.signals, crisis_type.value)
    severity = confidence_to_severity(confidence)

    location = batch.primary_location or (
        batch.signals[0].location if batch.signals else "Unknown"
    )

    # Severity escalation / dedup: if we've seen >=1 prior detection
    # (i.e. this is at least the 2nd occurrence) of the same (location, type)
    # within the trace window, bump the severity one rung.
    prior_count = _recent_event_signature_count(
        location or "", crisis_type.value, window_minutes=5
    )
    escalated = False
    if prior_count >= 1 and severity != Severity.CRITICAL:
        severity = _bump_severity(severity)
        escalated = True

    parts = [
        f"{crisis_type.value.upper()} detected at {location} with {confidence:.0%} confidence",
        f"from {len(batch.signals)} signal(s)",
    ]
    if breakdown.get("weather_corroboration_bonus", 0) > 0:
        parts.append("weather alert corroborated")
    if breakdown.get("traffic_corroboration_bonus", 0) > 0:
        parts.append("traffic blockage corroborated")
    if breakdown.get("engagement_bonus", 0) > 0:
        parts.append("high social engagement")
    if escalated:
        parts.append(f"escalated (recurrence #{prior_count + 1} in 5 min)")
    explanation = ". ".join(parts) + "."

    event = CrisisEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        crisis_type=crisis_type,
        location=location or "Unknown",
        confidence=confidence,
        severity=severity,
        signals=batch.signals,
        explanation=explanation,
        detected_at=datetime.now(timezone.utc),
    )

    elapsed_ms = int((time.time() - start) * 1000)

    # Log trace step
    latest = trace_store.get_latest()
    run_id = latest["run_id"] if latest and latest.get("status") == "running" else "unknown"
    output_payload = event.model_dump(mode="json")
    output_payload["breakdown"] = breakdown
    output_payload["escalated"] = escalated
    output_payload["prior_occurrences_5min"] = prior_count

    trace_store.log_step(
        run_id=run_id,
        agent="event-detection-agent",
        step="detect_crisis",
        input_data={"batch_id": batch.batch_id, "signal_count": len(batch.signals)},
        output_data=output_payload,
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="event-detection-agent",
        step="detect_crisis",
        input_data={"batch_id": batch.batch_id},
        output_data={
            "event_id": event.event_id,
            "crisis_type": event.crisis_type.value,
            "confidence": event.confidence,
            "escalated": escalated,
        },
        duration_ms=elapsed_ms,
    )

    return event
