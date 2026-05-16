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

from routers.detect import compute_confidence, confidence_to_severity, detect_crisis_type
from models.signal import CrisisType, Severity, Signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signal(source: str, content: str, keywords: list[str], severity_hint: str = "low") -> Signal:
    return Signal(
        signal_id=f"sig_{source}",
        source=source,
        content=content,
        keywords=keywords,
        severity_hint=severity_hint,
        location="G-10",
    )


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
