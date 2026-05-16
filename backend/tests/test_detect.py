"""Tests for the Event Detection Agent.

Covers:
  - Confidence scoring (single-source low vs multi-source high)
  - Crisis type classification (flood, heatwave, blockage, accident)
  - Severity escalation based on confidence thresholds
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routers.detect import (
    compute_confidence,
    compute_confidence_detailed,
    confidence_to_severity,
    detect_crisis_type,
)
from models.signal import CrisisType, Severity, Signal, SignalBatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signal(
    source: str,
    content: str,
    keywords: list[str],
    severity_hint: str = "low",
    location: str = "G-10",
) -> Signal:
    return Signal(
        signal_id=f"sig_{source}",
        source=source,
        content=content,
        keywords=keywords,
        severity_hint=severity_hint,
        location=location,
    )


def _dict_signal(
    source: str,
    content: str = "",
    location: str = "G-10",
    severity_hint: str = "low",
    engagement: int = 0,
    keywords: list[str] | None = None,
) -> dict:
    """Dict-shaped signal so we can attach metadata/engagement easily."""
    return {
        "signal_id": f"sig_{source}",
        "source": source,
        "content": content,
        "location": location,
        "severity_hint": severity_hint,
        "keywords": keywords or [],
        "metadata": {"engagement": engagement},
    }


# ---------------------------------------------------------------------------
# Confidence Scoring
# ---------------------------------------------------------------------------

class TestComputeConfidence:
    def test_single_source_low_confidence(self):
        """One signal from one source with no severity hint → low confidence."""
        signals = [_signal("social", "some rain", ["rain"])]
        score = compute_confidence(signals, "flood")
        assert score < 0.4, f"Expected < 0.4, got {score}"

    def test_two_signals_same_source_medium(self):
        """Two signals from the same source → still only 1 source bonus."""
        signals = [
            _signal("social", "flood in G-10", ["flood"]),
            _signal("social", "pani bhar gaya", ["pani"]),
        ]
        score = compute_confidence(signals, "flood")
        # 2-signal base (0.15) + 1 source (no bonus) = 0.15
        assert score < 0.5

    def test_multi_source_high_confidence(self):
        """Three signals from three distinct sources → high confidence."""
        signals = [
            _signal("social", "flash flood G-10", ["flood", "flash flood"], "high"),
            _signal("weather", "heavy rain warning", ["rain", "flood"], "high"),
            _signal("traffic", "roads submerged", ["flood", "waterlogging"], "medium"),
        ]
        score = compute_confidence(signals, "flood")
        assert score >= 0.6, f"Expected >= 0.6, got {score}"

    def test_high_severity_boost(self):
        """A single high-severity signal should boost confidence."""
        base = compute_confidence([_signal("social", "rain", ["rain"])], "flood")
        boosted = compute_confidence(
            [_signal("social", "flash flood", ["flood", "flash flood"], "high")], "flood"
        )
        assert boosted > base

    def test_confidence_capped_at_one(self):
        """Confidence must never exceed 1.0."""
        signals = [
            _signal("social", "critical flood", ["flood"], "high"),
            _signal("weather", "severe flood", ["flood"], "high"),
            _signal("traffic", "roads blocked", ["flood"], "high"),
            _signal("emergency", "rescue needed", ["flood"], "high"),
        ]
        score = compute_confidence(signals, "flood")
        assert score <= 1.0


# ---------------------------------------------------------------------------
# Severity Escalation
# ---------------------------------------------------------------------------

class TestConfidenceToSeverity:
    def test_critical_above_80(self):
        assert confidence_to_severity(0.85) == Severity.CRITICAL
        assert confidence_to_severity(1.0) == Severity.CRITICAL

    def test_high_60_to_80(self):
        assert confidence_to_severity(0.65) == Severity.HIGH
        assert confidence_to_severity(0.79) == Severity.HIGH

    def test_medium_40_to_60(self):
        assert confidence_to_severity(0.45) == Severity.MEDIUM
        assert confidence_to_severity(0.59) == Severity.MEDIUM

    def test_low_below_40(self):
        assert confidence_to_severity(0.0) == Severity.LOW
        assert confidence_to_severity(0.39) == Severity.LOW


# ---------------------------------------------------------------------------
# Crisis Type Detection
# ---------------------------------------------------------------------------

class TestDetectCrisisType:
    def test_flood_detection(self):
        """Signals with flood/sailaab/pani keywords → FLOOD."""
        signals = [
            _signal("social", "G-10 mein pani bhar gaya", ["flood", "pani"]),
            _signal("weather", "flash flood warning issued", ["flash flood", "rain"]),
        ]
        assert detect_crisis_type(signals) == CrisisType.FLOOD

    def test_heatwave_detection(self):
        """Signals with heat/garmi/degrees keywords → HEATWAVE."""
        signals = [
            _signal("social", "48 degrees in Jacobabad, people collapsing", ["heat", "degrees", "collapsing"]),
            _signal("social", "garmi se behosh ho rahe hain", ["garmi", "behosh"]),
        ]
        assert detect_crisis_type(signals) == CrisisType.HEATWAVE

    def test_blockage_detection(self):
        """Signals with blocked/jam/congestion keywords → BLOCKAGE."""
        signals = [
            _signal("traffic", "road completely jammed", ["blocked", "jam", "congestion"]),
            _signal("social", "protest blocking Shahrah-e-Faisal", ["blockage", "protest"]),
        ]
        assert detect_crisis_type(signals) == CrisisType.BLOCKAGE

    def test_accident_detection(self):
        """Signals with accident/crash keywords → ACCIDENT."""
        signals = [
            _signal("social", "major accident on GT Road", ["accident", "crash"]),
            _signal("emergency", "multi-vehicle collision reported", ["collision", "accident"]),
        ]
        assert detect_crisis_type(signals) == CrisisType.ACCIDENT

    def test_flood_dominates_when_more_keywords(self):
        """When flood keywords outnumber others, FLOOD wins."""
        signals = [
            _signal("social", "heavy rain and flash flood", ["rain", "flood", "flash flood", "waterlogging"]),
            _signal("weather", "flooding continues", ["flood", "baarish"]),
            _signal("traffic", "jam due to floods", ["jam", "flood"]),
        ]
        result = detect_crisis_type(signals)
        assert result == CrisisType.FLOOD


# ---------------------------------------------------------------------------
# Engagement Bonus
# ---------------------------------------------------------------------------

class TestEngagementBonus:
    def test_no_engagement_no_bonus(self):
        signals = [_dict_signal("social", engagement=0)]
        _, br = compute_confidence_detailed(signals, "flood")
        assert br["engagement_bonus"] == 0.0

    def test_engagement_500_to_2000(self):
        signals = [_dict_signal("social", engagement=1200)]
        _, br = compute_confidence_detailed(signals, "flood")
        assert br["engagement_bonus"] == 0.05

    def test_engagement_above_2000(self):
        signals = [_dict_signal("social", engagement=3500)]
        _, br = compute_confidence_detailed(signals, "flood")
        assert br["engagement_bonus"] == 0.10

    def test_engagement_above_5000(self):
        signals = [_dict_signal("social", engagement=8000)]
        _, br = compute_confidence_detailed(signals, "flood")
        assert br["engagement_bonus"] == 0.15


# ---------------------------------------------------------------------------
# Weather corroboration
# ---------------------------------------------------------------------------

class TestWeatherCorroboration:
    def test_g10_flood_matches_rain_alert(self):
        signals = [
            _signal("social", "flood G-10", ["flood", "flash flood"], "high", location="G-10"),
        ]
        _, br = compute_confidence_detailed(signals, "flood")
        assert br["weather_corroboration_bonus"] == 0.15
        assert br["weather_matches"]

    def test_karachi_heat_matches_heat_advisory(self):
        signals = [_signal("social", "heat", ["heat"], "high", location="Karachi")]
        _, br = compute_confidence_detailed(signals, "heatwave")
        assert br["weather_corroboration_bonus"] == 0.15

    def test_no_match_when_crisis_type_differs(self):
        signals = [_signal("social", "fire", ["fire"], "high", location="G-10")]
        _, br = compute_confidence_detailed(signals, "fire")
        assert br["weather_corroboration_bonus"] == 0.0


# ---------------------------------------------------------------------------
# Traffic corroboration
# ---------------------------------------------------------------------------

class TestTrafficCorroboration:
    def test_shahrah_e_faisal_blocked_matches(self):
        signals = [
            _signal(
                "social",
                "Shahrah-e-Faisal blocked",
                ["blocked"],
                "high",
                location="Shahrah-e-Faisal",
            ),
        ]
        _, br = compute_confidence_detailed(signals, "blockage")
        assert br["traffic_corroboration_bonus"] == 0.15
        assert br["traffic_matches"]

    def test_route_not_blocked_no_bonus(self):
        signals = [_signal("social", "free", ["traffic"], "low", location="Margalla Road")]
        _, br = compute_confidence_detailed(signals, "blockage")
        assert br["traffic_corroboration_bonus"] == 0.0


# ---------------------------------------------------------------------------
# Multi-source CRITICAL escalation – the Track 2.2 acceptance scenario
# ---------------------------------------------------------------------------

class TestMultiSourceCritical:
    def test_g10_flood_with_weather_and_traffic_is_critical(self):
        signals = [
            _signal("social", "flash flood G-10", ["flood", "flash flood"], "high", location="G-10"),
            _signal("weather", "heavy rain warning", ["flood", "rain"], "high", location="G-10"),
            _signal("traffic", "Kashmir Highway blocked", ["blockage"], "high", location="Kashmir Highway"),
        ]
        score, br = compute_confidence_detailed(signals, "flood")
        # base 0.30 + sources 0.40 + severity 0.30 + weather 0.15 = 1.0 (capped)
        assert score >= 0.85
        assert confidence_to_severity(score) == Severity.CRITICAL


# ---------------------------------------------------------------------------
# Severity escalation via /detect/crisis (uses trace history)
# ---------------------------------------------------------------------------

class TestSeverityEscalation:
    def test_repeated_event_bumps_severity(self, client):
        batch_payload = {
            "batch_id": "batch_test_1",
            "primary_location": "F-7",
            "signals": [
                {
                    "signal_id": "sig1",
                    "source": "social",
                    "content": "small flood F-7",
                    "location": "F-7",
                    "severity_hint": "medium",
                    "keywords": ["flood"],
                    "language": "en",
                }
            ],
        }
        r1 = client.post("/detect/crisis", json=batch_payload)
        assert r1.status_code == 200
        first = r1.json()
        # Second call with same signature should escalate
        batch_payload["batch_id"] = "batch_test_2"
        r2 = client.post("/detect/crisis", json=batch_payload)
        assert r2.status_code == 200
        second = r2.json()
        ladder = ["low", "medium", "high", "critical"]
        assert ladder.index(second["severity"]) >= ladder.index(first["severity"])
