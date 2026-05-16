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
    "mein", "gaya", "gayi", "gaye", "hai", "hain", "gaari", "gaariyan",
    "pani", "phans", "bhar", "raha", "rahi", "rahe", "hua", "hui",
    "shadeed", "baarish", "sadak", "sadkein", "doob", "garmi", "behosh",
    "gir", "toofani", "toofan", "hawa", "bijli", "khamba", "nala",
    "ubhal", "dukano", "dukan", "log", "ghus", "aaya", "aayi",
    "dhamaka", "aag", "zalzala", "jhatke", "chhat", "khayi",
    "tasadum", "zakhmi", "halaak", "musafir", "firing", "ehtjaj",
    "se", "ka", "ki", "ko", "ne", "par", "pe", "ho", "kar",
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
    # Major cities
    "Karachi Coast", "Karachi Airport", "Karachi Old City", "Karachi Port", "Karachi",
    "Lahore Motorway", "Lahore",
    "Islamabad Business District", "Islamabad",
    "Rawalpindi Cantt", "Rawalpindi",
    "Peshawar", "Quetta", "Multan", "Bahawalpur", "Sukkur", "Hyderabad",
    "Faisalabad", "Sialkot", "Sialkot Airport", "Gujranwala", "Sargodha",
    "Abbottabad", "Mansehra", "Mardan", "Nowshera", "Chitral", "Hunza",
    "Mingora", "Hangu", "Kohat", "Bannu", "DG Khan", "Larkana",
    "Larkana District", "Mirpur Khas", "Khanewal", "Sahiwal", "Lodhran",
    "Rahim Yar Khan", "Hafizabad", "Chakwal", "Hazara", "Kasur",
    "Murree Road", "Murree Expressway", "Murree", "Thar",
    # Islamabad sectors
    "G-6", "G-7", "G-9", "G-10", "G-11", "G-12", "G-13",
    "F-6", "F-7", "F-8", "F-9", "F-10", "F-11",
    "I-8", "I-9", "I-10", "I-11",
    "E-7", "E-11",
    # Roads / landmarks
    "George Town", "Shahrah-e-Faisal", "Blue Area",
    "Margalla Road", "Margalla", "IJP Road", "Constitution Avenue",
    "Srinagar Highway", "Islamabad Expressway", "Expressway",
    "GT Road Peshawar", "GT Road", "Faizabad", "Kashmir Highway",
    "Saddar Rawalpindi", "Saddar", "Pir Wadhai", "Pindora",
    "Wapda House", "Diplomatic Enclave", "PIMS Islamabad",
    # Lahore landmarks
    "Mall Road Lahore", "Mall Road", "Liberty Roundabout",
    "Data Darbar", "Garden Town", "Johar Town",
    # Karachi landmarks
    "Tariq Road", "Lyari Expressway", "Lyari", "Liaquatabad",
    "Korangi Road", "Super Highway", "Mai Kolachi", "Defence Phase 8",
    "DHA Phase 5", "Gulshan-e-Iqbal", "Orangi Town", "Bahadurabad",
    "Sharae Quaideen", "JPMC Karachi", "PIA Office Karachi",
    "Bahria Town Phase 7", "Bahria Town", "Iqra University",
    # Highways / motorways
    "Motorway M-1", "Motorway M-2", "Motorway M-3",
    "N-5 Highway", "N-25 Highway",
    "Karakoram Highway", "Ring Road",
    # Other places mentioned in mock data
    "Jacobabad", "Naran-Kaghan", "Naran", "Kaghan",
    "Northern Pakistan", "Nationwide", "Punjab Rural",
    "Cantt Station", "Sohni Dharti Bridge",
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
    "accident", "collision", "collapse", "collapsed", "fire", "aag",
    "shadeed", "doob", "submerged", "behosh", "collapsing", "sparks",
    "gir gaya", "gir gaye", "ubhal", "ghus aaya",
    "dhamaka", "blast", "explosion", "exploded",
    "zalzala", "earthquake", "tremors", "jhatke",
    "landslide", "cyclone", "tornado", "tornado dekha",
    "halaak", "dead", "killed", "casualty", "casualties",
    "critical", "emergency", "urgent", "rescue",
    "stampede", "stranded", "trapped",
    "chhat gir", "cylinder blast", "firing", "bomb",
    "tasadum", "zakhmi", "injured", "burning",
    "evacuation", "outbreak", "epidemic",
]

MEDIUM_KEYWORDS = [
    "blocked", "block", "slow", "congestion", "congested", "delay", "delayed",
    "jam", "jammed", "waterlogging", "waterlogged", "protest", "riot",
    "smog", "dust storm", "hailstorm", "windstorm", "snowfall",
    "power outage", "load shedding", "load-shedding", "blackout",
    "leak", "leakage", "sewerage", "overflow",
    "ehtjaj", "bandh", "band",
]

LOW_KEYWORDS = [
    "rain", "baarish", "traffic", "hawa", "fog", "drizzle",
    "humid", "humidity", "windy", "cloudy",
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
    # Flood
    "flood", "flash flood", "pani", "bhar", "doob", "submerged",
    "waterlogging", "waterlogged", "nala", "ubhal", "baarish", "rain",
    "river", "overflow", "darya",
    # Heatwave
    "heatwave", "garmi", "heat", "heatstroke", "degrees", "temperature",
    "collapsing", "behosh", "cooling",
    # Blockage / traffic
    "blocked", "block", "jam", "jammed", "blockage", "congestion",
    "protest", "riot", "stranded", "diverted",
    # Accident
    "accident", "hadsa", "crash", "collision", "tasadum", "pile-up",
    "overturned", "derailed",
    # Fire
    "fire", "aag", "burning", "smoke", "flames", "cylinder blast",
    "blaze",
    # Earthquake / structural
    "zalzala", "earthquake", "tremors", "jhatke", "magnitude",
    "collapse", "collapsed", "sinkhole", "chhat gir",
    # Storm / weather
    "cyclone", "tornado", "landslide", "hailstorm", "windstorm",
    "dust storm", "snowfall", "toofan", "smog",
    # Infrastructure
    "power line", "bijli", "khamba", "sparks", "outage", "blackout",
    "leak", "leakage", "sewerage", "gas leak", "transformer",
    # Security / blast
    "dhamaka", "blast", "explosion", "bomb", "firing", "attack",
    # Medical / public health
    "dengue", "outbreak", "oxygen shortage", "hospital",
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


@router.post("/auto", response_model=SignalBatch, summary="Auto-ingest from weather + traffic mocks")
async def ingest_auto(location_filter: Optional[str] = None):
    """Pull simulated weather alerts and blocked traffic routes, normalise
    them into signals, buffer them, and return a multi-source ``SignalBatch``.

    Used by the demo to trigger multi-source corroboration in the Event
    Detection Agent without needing hand-crafted POSTs.  Optionally filter
    by ``location_filter`` substring (e.g. "Karachi") to scope the signals.
    """
    import json
    from pathlib import Path

    start = time.time()
    run_id = trace_store.start_run(signal_text="[auto-ingest]")

    data_dir = Path(__file__).resolve().parent.parent / "data"
    raw_inputs: List[RawSignalInput] = []

    # ── Weather alerts → signals ──────────────────────────────────────────
    try:
        weather = json.loads((data_dir / "weather_mock.json").read_text(encoding="utf-8"))
        for alert in weather.get("alerts", []):
            for region in alert.get("regions", []):
                if location_filter and location_filter.lower() not in region.lower():
                    continue
                raw_inputs.append(
                    RawSignalInput(
                        source="weather",
                        text=f"{alert.get('event', 'Weather Alert')} in {region}: {alert.get('description', '')}",
                        metadata={"geo": region, "severity": alert.get("severity")},
                    )
                )
    except Exception:
        pass

    # ── Traffic blocked routes → signals ─────────────────────────────────
    try:
        traffic = json.loads((data_dir / "traffic_mock.json").read_text(encoding="utf-8"))
        for route in traffic.get("routes", []):
            if route.get("status") != "blocked":
                continue
            city = route.get("city", "")
            name = route.get("name", "")
            if location_filter and location_filter.lower() not in (city + " " + name).lower():
                continue
            incident = route.get("incident") or "blockage"
            raw_inputs.append(
                RawSignalInput(
                    source="traffic",
                    text=f"{name} ({city}) is blocked. Incident: {incident}. Travel time {route.get('travel_time_min', 0)} min vs normal {route.get('normal_time_min', 0)} min.",
                    metadata={"geo": name, "city": city},
                )
            )
    except Exception:
        pass

    # ── Process each → buffer → batch ─────────────────────────────────────
    new_signals: List[Signal] = []
    for raw in raw_inputs:
        signal = process_signal(raw)
        new_signals.append(signal)
        _signal_buffer.append(signal)
        if len(_signal_buffer) > _BUFFER_SIZE:
            _signal_buffer.pop(0)

    batch = _build_batch(list(_signal_buffer))
    elapsed_ms = int((time.time() - start) * 1000)

    trace_store.log_step(
        run_id=run_id,
        agent="signal-ingestion-agent",
        step="auto_ingest",
        input_data={"location_filter": location_filter, "candidates": len(raw_inputs)},
        output_data=batch.model_dump(mode="json"),
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="signal-ingestion-agent",
        step="auto_ingest",
        input_data={"location_filter": location_filter},
        output_data={"batch_id": batch.batch_id, "signal_count": len(batch.signals), "new_signals": len(new_signals)},
        duration_ms=elapsed_ms,
    )

    return batch


@router.post("/clear", summary="Clear the signal buffer")
async def clear_buffer():
    """Clear the in-memory signal buffer."""
    _signal_buffer.clear()
    return {"status": "cleared", "buffer_size": 0}
