"""Signal Ingestion Agent – POST /ingest/signal

Owned by Anas Bin Rashid.

Accepts raw text signals (Urdu or English) from any source, normalises
them into a canonical ``Signal`` record, aggregates them into a
``SignalBatch``, and forwards the batch to the Event Detection Agent.

Processing pipeline per signal:
  1. Detect language (Urdu / English) via keyword matching
  2. Extract location (Pakistani sectors / named locations)
  3. Tag severity (HIGH / MEDIUM / LOW) via keyword intensity
  4. Extract crisis-related keywords
  5. Append to in-memory buffer → flush as SignalBatch
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter

from models.signal import RawSignalInput, Signal, SignalBatch
from services.trace_store import trace_store
from utils.logger import log_agent_step

router = APIRouter(prefix="/ingest", tags=["Signal Ingestion"])

# ---------------------------------------------------------------------------
# In-memory signal buffer (last N signals)
# ---------------------------------------------------------------------------
_BUFFER_SIZE = 5
_signal_buffer: List[Signal] = []

# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

# Common Urdu words that appear in romanised social media posts
URDU_KEYWORDS = [
    "mein", "gaya", "hai", "gaari", "gaariyan", "pani", "phans",
    "bhar", "raha", "hua", "hain", "shadeed", "baarish", "sadak",
    "sadkein", "doob", "garmi", "behosh", "gir", "toofani",
    "hawa", "bijli", "khamba", "nala", "ubhal", "dukano",
    "log", "rahe", "ghus", "aaya",
]

# Unicode range for Arabic/Urdu script characters
_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")


def detect_language(text: str) -> str:
    """Return ``'ur'`` if the text is likely Urdu, else ``'en'``."""
    # Check for Urdu script characters first
    if _URDU_SCRIPT_RE.search(text):
        return "ur"
    # Fall back to romanised keyword matching
    lower = text.lower()
    matches = sum(1 for kw in URDU_KEYWORDS if kw in lower)
    return "ur" if matches >= 2 else "en"


# ---------------------------------------------------------------------------
# Location Extraction
# ---------------------------------------------------------------------------

# Regex for Islamabad-style sector codes: G-10, F-6, I-8, E-11, etc.
_SECTOR_RE = re.compile(r"\b([GFEI]-\d{1,2})\b", re.IGNORECASE)

# Named Pakistani locations / roads
NAMED_LOCATIONS = [
    "George Town", "Karachi", "Lahore", "Islamabad", "Rawalpindi",
    "Shahrah-e-Faisal", "Blue Area", "Margalla Road", "Margalla",
    "IJP Road", "Constitution Avenue", "Srinagar Highway",
    "Expressway", "GT Road", "Faizabad", "Jacobabad",
    "I-9", "I-8", "G-10", "G-9", "F-6", "F-7", "F-8", "E-11", "E-7",
]


def extract_location(text: str) -> Optional[str]:
    """Return the first recognised Pakistani location from *text*."""
    # Try sector code first
    m = _SECTOR_RE.search(text)
    if m:
        return m.group(1).upper()

    # Then try named locations (case-insensitive)
    lower = text.lower()
    for loc in NAMED_LOCATIONS:
        if loc.lower() in lower:
            return loc
    return None


# ---------------------------------------------------------------------------
# Severity Keyword Tagger
# ---------------------------------------------------------------------------

HIGH_KEYWORDS = [
    "flash flood", "pani bhar", "phans gayi", "phans gaye",
    "accident", "collapse", "fire", "shadeed", "doob",
    "behosh", "collapsing", "sparks", "gir gaya", "gir gaye",
    "ubhal", "ghus aaya",
]

MEDIUM_KEYWORDS = [
    "blocked", "slow", "congestion", "delay", "jam", "jammed",
    "stranded", "waterlogging", "protest",
]

LOW_KEYWORDS = [
    "rain", "baarish", "traffic", "hawa",
]


def tag_severity(text: str) -> str:
    """Return ``'high'``, ``'medium'``, or ``'low'`` based on keywords."""
    lower = text.lower()
    for kw in HIGH_KEYWORDS:
        if kw in lower:
            return "high"
    for kw in MEDIUM_KEYWORDS:
        if kw in lower:
            return "medium"
    for kw in LOW_KEYWORDS:
        if kw in lower:
            return "low"
    return "low"


# ---------------------------------------------------------------------------
# Keyword Extractor
# ---------------------------------------------------------------------------

CRISIS_KEYWORDS = {
    # Flood-related
    "flood", "flash flood", "pani", "bhar", "doob", "waterlogging",
    "nala", "ubhal", "baarish", "rain",
    # Heatwave-related
    "heatwave", "garmi", "heat", "degrees", "collapsing", "behosh",
    # Blockage-related
    "blocked", "jam", "jammed", "blockage", "congestion", "protest",
    # Accident-related
    "accident", "hadsa", "crash", "collision",
    # Infrastructure
    "fire", "collapse", "power line", "bijli", "khamba", "sparks",
}


def extract_keywords(text: str) -> List[str]:
    """Return crisis-related keywords found in the text."""
    lower = text.lower()
    found = [kw for kw in CRISIS_KEYWORDS if kw in lower]
    return sorted(set(found))


# ---------------------------------------------------------------------------
# Signal Processing Pipeline
# ---------------------------------------------------------------------------

def process_signal(raw: RawSignalInput) -> Signal:
    """Run the full normalisation pipeline on a single raw signal."""
    language = detect_language(raw.text)
    location = extract_location(raw.text)
    severity = tag_severity(raw.text)
    keywords = extract_keywords(raw.text)

    # Override location from metadata if provided
    if not location and raw.metadata and raw.metadata.get("geo"):
        location = raw.metadata["geo"]

    return Signal(
        signal_id=f"sig_{uuid.uuid4().hex[:8]}",
        source=raw.source,
        content=raw.text,
        location=location,
        timestamp=datetime.now(timezone.utc),
        language=language,
        severity_hint=severity,
        keywords=keywords,
    )


def _build_batch(signals: List[Signal]) -> SignalBatch:
    """Create a SignalBatch from a list of signals."""
    # Primary location = most common location in the batch
    locations = [s.location for s in signals if s.location]
    primary = max(set(locations), key=locations.count) if locations else None

    return SignalBatch(
        batch_id=f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}",
        signals=signals,
        primary_location=primary,
    )


# ---------------------------------------------------------------------------
# API Endpoint
# ---------------------------------------------------------------------------

@router.post("/signal", response_model=SignalBatch, summary="Ingest a raw signal")
async def ingest_signal(raw: RawSignalInput):
    """Accept a raw signal, normalise it, buffer it, and return a SignalBatch.

    The returned batch contains the current signal buffer (up to 5 most-recent
    signals).  This batch is what the Event Detection Agent consumes.
    """
    start = time.time()

    # Start a trace run for this pipeline invocation
    run_id = trace_store.start_run(signal_text=raw.text)

    # Process the signal
    signal = process_signal(raw)

    # Add to buffer (ring buffer of last N signals)
    _signal_buffer.append(signal)
    if len(_signal_buffer) > _BUFFER_SIZE:
        _signal_buffer.pop(0)

    # Build the batch from current buffer
    batch = _build_batch(list(_signal_buffer))

    elapsed_ms = int((time.time() - start) * 1000)

    # Log the agent step
    trace_store.log_step(
        run_id=run_id,
        agent="signal-ingestion-agent",
        step="normalise_signal",
        input_data=raw.model_dump(),
        output_data=batch.model_dump(mode="json"),
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="signal-ingestion-agent",
        step="normalise_signal",
        input_data=raw.model_dump(),
        output_data={"batch_id": batch.batch_id, "signal_count": len(batch.signals)},
        duration_ms=elapsed_ms,
    )

    return batch


@router.post("/clear", summary="Clear the signal buffer")
async def clear_buffer():
    """Clear the in-memory signal buffer."""
    _signal_buffer.clear()
    return {"status": "cleared", "buffer_size": 0}
