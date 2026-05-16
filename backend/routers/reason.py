"""Reasoning & Analysis Agent – POST /reason/analyse

Stub router with fallback cache. Full Gemini integration by Arshman.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter

from models.signal import CrisisAnalysis, CrisisEvent
from services.cache import analysis_cache
from services.trace_store import trace_store
from utils.logger import log_agent_step

router = APIRouter(prefix="/reason", tags=["Reasoning & Analysis"])

# ---------------------------------------------------------------------------
# Groq client configuration
# ---------------------------------------------------------------------------

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "5"))
GROQ_MAX_RETRIES = 1

_groq_client = None


def _get_groq_client():
    """Lazily build a Groq client. Returns None if unavailable."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq

        _groq_client = Groq(api_key=api_key, timeout=GROQ_TIMEOUT_SECONDS)
        return _groq_client
    except Exception:
        return None


def _build_prompt(event: CrisisEvent) -> str:
    """Compose the prompt sent to the LLM, embedding signal evidence."""
    signal_lines = []
    for s in event.signals[:8]:
        loc = getattr(s, "location", None) or "unknown"
        lang = getattr(s, "language", None) or "en"
        content = (getattr(s, "content", "") or "")[:280]
        signal_lines.append(f"- [{s.source}|{lang}|{loc}] {content}")
    signals_block = "\n".join(signal_lines) if signal_lines else "- (no signal evidence)"

    return (
        "You are CIRO's Reasoning Agent. Given a detected crisis event and the\n"
        "raw signals that produced it, produce a concise, judge-ready impact\n"
        "analysis as STRICT JSON with this exact schema:\n"
        "{\n"
        '  "impact": [string, ...],            // 3-5 short bullets, plain English\n'
        '  "affected_population": integer,      // realistic estimate\n'
        '  "infrastructure_at_risk": [string], // 2-6 items\n'
        '  "urgency": "immediate" | "within_hour" | "monitoring",\n'
        '  "summary": string                    // one-paragraph briefing\n'
        "}\n\n"
        f"Crisis type: {event.crisis_type.value}\n"
        f"Location: {event.location}\n"
        f"Severity: {event.severity.value}\n"
        f"Confidence: {event.confidence:.2f}\n"
        f"Signal count: {len(event.signals)}\n"
        f"Signals (may be Urdu or English):\n{signals_block}\n\n"
        "Return ONLY the JSON object. No commentary, no markdown."
    )


def _coerce_analysis_payload(data: dict) -> dict:
    """Normalise an LLM response into the analysis schema."""
    impact = data.get("impact") or []
    if isinstance(impact, str):
        impact = [impact]
    impact = [str(x) for x in impact][:8]

    infra = data.get("infrastructure_at_risk") or []
    if isinstance(infra, str):
        infra = [infra]
    infra = [str(x) for x in infra][:10]

    try:
        affected = int(data.get("affected_population") or 0)
    except (TypeError, ValueError):
        affected = 0

    urgency = str(data.get("urgency") or "monitoring").lower()
    if urgency not in {"immediate", "within_hour", "monitoring"}:
        urgency = "monitoring"

    return {
        "impact": impact,
        "affected_population": affected,
        "infrastructure_at_risk": infra,
        "urgency": urgency,
        "summary": str(data.get("summary") or ""),
    }


def _call_groq(event: CrisisEvent) -> Optional[dict]:
    """Call Groq with one retry. Returns None on any failure."""
    client = _get_groq_client()
    if client is None:
        return None

    prompt = _build_prompt(event)
    last_err: Optional[Exception] = None
    for attempt in range(GROQ_MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=600,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a crisis-analysis assistant for Pakistan urban emergencies. "
                            "Always reply with strict JSON matching the requested schema."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = resp.choices[0].message.content or "{}"
            data = json.loads(content)
            return _coerce_analysis_payload(data)
        except Exception as exc:  # network, json, rate limit, etc.
            last_err = exc
            continue
    return None

# ---------------------------------------------------------------------------
# Fallback Cache – pre-populated for 5 demo scenarios
# ---------------------------------------------------------------------------

FALLBACK_CACHE = {
    ("flood", "high"): {
        "impact": [
            "Residential areas in G-10 submerged with 2-3 feet of standing water",
            "Vehicular traffic completely halted on main arteries",
            "Risk of waterborne disease outbreak within 24-48 hours",
        ],
        "affected_population": 3200,
        "infrastructure_at_risk": ["roads", "drainage", "power grid", "telecom towers"],
        "urgency": "immediate",
        "summary": "Severe flash flooding in G-10 sector requires immediate rescue and evacuation operations. Infrastructure damage is significant.",
    },
    ("flood", "critical"): {
        "impact": [
            "Multiple sectors submerged with water levels exceeding 4 feet",
            "Complete gridlock across the city — thousands stranded",
            "Hospital access routes compromised",
            "Electrical infrastructure at risk of failure",
        ],
        "affected_population": 8500,
        "infrastructure_at_risk": ["roads", "hospitals", "power grid", "drainage", "bridges"],
        "urgency": "immediate",
        "summary": "Critical multi-sector flooding with life-threatening conditions. Multi-agency response required immediately.",
    },
    ("heatwave", "high"): {
        "impact": [
            "Temperature exceeding 48°C — extreme heatstroke risk",
            "Outdoor workers and elderly population at critical risk",
            "Power grid under strain from AC overload",
        ],
        "affected_population": 15000,
        "infrastructure_at_risk": ["power grid", "water supply", "public transport"],
        "urgency": "immediate",
        "summary": "Extreme heatwave in Jacobabad/Karachi region. Cooling centres and water distribution urgently needed.",
    },
    ("blockage", "medium"): {
        "impact": [
            "Major arterial road completely blocked",
            "Commuters experiencing 2+ hour delays",
            "Emergency vehicle access compromised",
        ],
        "affected_population": 5000,
        "infrastructure_at_risk": ["roads", "public transport"],
        "urgency": "within_hour",
        "summary": "Road blockage on Shahrah-e-Faisal causing severe disruption. Traffic rerouting required.",
    },
    ("accident", "high"): {
        "impact": [
            "Multi-vehicle collision causing road closure",
            "Injured persons requiring immediate medical attention",
            "Secondary congestion building on alternate routes",
        ],
        "affected_population": 800,
        "infrastructure_at_risk": ["roads"],
        "urgency": "immediate",
        "summary": "Serious accident requiring emergency medical response and road closure management.",
    },
    ("flood", "low"): {
        "impact": [
            "Minor waterlogging reported in isolated areas",
            "Traffic slightly slower than usual",
        ],
        "affected_population": 200,
        "infrastructure_at_risk": ["drainage"],
        "urgency": "monitoring",
        "summary": "Low-level rainfall causing minor waterlogging. Situation under monitoring.",
    },
    ("fire", "high"): {
        "impact": [
            "Active fire spreading across multiple structures",
            "Heavy smoke reducing visibility in adjacent sectors",
            "Risk of cylinder/transformer secondary explosions",
        ],
        "affected_population": 1500,
        "infrastructure_at_risk": ["buildings", "power grid", "roads"],
        "urgency": "immediate",
        "summary": "Major fire requires fire brigade, ambulance, and road closure response.",
    },
    ("fire", "critical"): {
        "impact": [
            "Industrial-scale fire with multiple structures engulfed",
            "Toxic smoke plume affecting wider population",
            "Risk of cascading failures across power grid",
            "Mass casualty potential",
        ],
        "affected_population": 5000,
        "infrastructure_at_risk": ["buildings", "power grid", "gas lines", "telecom"],
        "urgency": "immediate",
        "summary": "Critical fire incident demands multi-agency response and evacuation perimeter.",
    },
    ("earthquake", "high"): {
        "impact": [
            "Structural damage reported across affected zone",
            "Aftershock risk continues for next 24-48 hours",
            "Possible trapped persons in collapsed structures",
        ],
        "affected_population": 4000,
        "infrastructure_at_risk": ["buildings", "bridges", "roads", "power grid"],
        "urgency": "immediate",
        "summary": "Seismic event requires search-and-rescue, structural assessment, and aftershock advisories.",
    },
    ("earthquake", "critical"): {
        "impact": [
            "Widespread structural collapse",
            "Mass casualties feared, hospitals receiving wounded",
            "Power, water, and telecom infrastructure compromised",
            "Strong aftershocks expected",
        ],
        "affected_population": 12000,
        "infrastructure_at_risk": ["buildings", "hospitals", "bridges", "power grid", "water supply", "telecom"],
        "urgency": "immediate",
        "summary": "Critical earthquake demands NDMA coordination, urban search and rescue, and field hospitals.",
    },
    ("storm", "high"): {
        "impact": [
            "High winds uprooting trees and damaging structures",
            "Power lines down across several sectors",
            "Travel hazardous on highways and bridges",
        ],
        "affected_population": 6000,
        "infrastructure_at_risk": ["power grid", "roads", "billboards", "trees"],
        "urgency": "immediate",
        "summary": "Severe storm warrants advisories, shelter activation, and route closures.",
    },
    ("storm", "critical"): {
        "impact": [
            "Cyclone-force winds with extreme rainfall",
            "Coastal flooding and storm surge expected",
            "Major infrastructure at risk including airport",
            "Mass evacuation may be required",
        ],
        "affected_population": 50000,
        "infrastructure_at_risk": ["coastline", "airport", "power grid", "telecom", "buildings"],
        "urgency": "immediate",
        "summary": "Critical cyclone demands evacuation of coastal areas and full disaster response activation.",
    },
    ("infrastructure", "high"): {
        "impact": [
            "Major utility failure affecting thousands of households",
            "Hospitals and critical facilities on backup power",
            "Risk of secondary incidents (fires, flooding) elevated",
        ],
        "affected_population": 8000,
        "infrastructure_at_risk": ["power grid", "water supply", "telecom"],
        "urgency": "within_hour",
        "summary": "Infrastructure failure requires WAPDA/utility coordination and citizen advisories.",
    },
    ("infrastructure", "critical"): {
        "impact": [
            "Cascading utility failures across multiple sectors",
            "Critical care facilities at risk of running out of backup power",
            "Communications partially down",
        ],
        "affected_population": 25000,
        "infrastructure_at_risk": ["power grid", "water supply", "hospitals", "telecom", "transport"],
        "urgency": "immediate",
        "summary": "Critical infrastructure crisis requires multi-utility coordination and emergency provisioning.",
    },
}


def _get_cached_analysis(crisis_type: str, severity: str) -> dict:
    """Look up the fallback cache by (crisis_type, severity)."""
    key = (crisis_type.lower(), severity.lower())
    if key in FALLBACK_CACHE:
        return FALLBACK_CACHE[key]
    # Fallback: try just the crisis type with any severity
    for k, v in FALLBACK_CACHE.items():
        if k[0] == crisis_type.lower():
            return v
    # Ultimate fallback
    return {
        "impact": [f"{crisis_type.capitalize()} event detected. Analysis pending."],
        "affected_population": 500,
        "infrastructure_at_risk": ["unknown"],
        "urgency": "monitoring",
        "summary": f"A {crisis_type} event has been detected. Further analysis required.",
    }


@router.post("/analyse", response_model=CrisisAnalysis, summary="AI analysis via Groq LLM")
async def analyse_crisis(event: CrisisEvent):
    """Analyse a crisis event using Groq's llama-3.3-70b-versatile.

    Strategy:
    1. Check the response cache keyed by (event_id, crisis_type, severity).
    2. On miss, call Groq with strict JSON output, 5s timeout, one retry.
    3. On any failure (no key, timeout, parse error), fall back to the
       pre-populated FALLBACK_CACHE so the demo never breaks.
    """
    start = time.time()

    cache_key = (event.event_id, event.crisis_type.value, event.severity.value)
    cached_payload = analysis_cache.get(cache_key)
    source = "cache"

    if cached_payload is None:
        source = "fallback"
        llm_payload = _call_groq(event)
        if llm_payload is not None:
            cached_payload = llm_payload
            source = "groq"
        else:
            cached_payload = _get_cached_analysis(
                event.crisis_type.value, event.severity.value
            )
        analysis_cache.set(cache_key, cached_payload)

    analysis = CrisisAnalysis(
        analysis_id=f"ana_{uuid.uuid4().hex[:8]}",
        event_id=event.event_id,
        impact=cached_payload["impact"],
        affected_population=cached_payload["affected_population"],
        infrastructure_at_risk=cached_payload["infrastructure_at_risk"],
        urgency=cached_payload["urgency"],
        summary=cached_payload["summary"],
    )

    elapsed_ms = int((time.time() - start) * 1000)

    # Log trace step
    latest = trace_store.get_latest()
    run_id = latest["run_id"] if latest and latest.get("status") == "running" else "unknown"
    trace_store.log_step(
        run_id=run_id,
        agent="reasoning-analysis-agent",
        step="analyse_crisis",
        input_data={
            "event_id": event.event_id,
            "crisis_type": event.crisis_type.value,
            "source": source,
        },
        output_data=analysis.model_dump(mode="json"),
        duration_ms=elapsed_ms,
    )
    log_agent_step(
        agent="reasoning-analysis-agent",
        step="analyse_crisis",
        input_data={"event_id": event.event_id, "source": source},
        output_data={"analysis_id": analysis.analysis_id, "urgency": analysis.urgency},
        duration_ms=elapsed_ms,
    )

    return analysis


@router.get("/cache/stats", summary="Inspect the reasoning response cache")
async def cache_stats():
    """Return hit/miss stats for the in-memory analysis cache."""
    return analysis_cache.stats()


@router.post("/cache/clear", summary="Clear the reasoning response cache")
async def cache_clear():
    """Drop every cached LLM analysis (used by demo reset)."""
    analysis_cache.clear()
    return {"status": "cleared"}
