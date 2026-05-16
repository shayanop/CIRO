"""Tests for the Signal Ingestion Agent.

Covers:
  - Urdu input detection
  - English input detection
  - Location extraction (sector codes and named locations)
  - Severity tagging
  - Mixed source batching
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the backend directory is on the import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routers.ingest import (
    detect_language,
    extract_keywords,
    extract_location,
    process_signal,
    tag_severity,
)
from models.signal import RawSignalInput


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    def test_urdu_romanised_text(self):
        """Romanised Urdu text with ≥2 keywords should be detected as Urdu."""
        text = "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"
        assert detect_language(text) == "ur"

    def test_english_text(self):
        """Standard English text should be detected as English."""
        text = "Flash flood happening at George Town for past 30 mins"
        assert detect_language(text) == "en"

    def test_short_english(self):
        """Short English text with no Urdu keywords."""
        text = "Traffic jam on highway"
        assert detect_language(text) == "en"

    def test_mixed_but_mostly_urdu(self):
        """Text with multiple Urdu keywords should be detected as Urdu."""
        text = "Shadeed baarish mein sadkein doob gayi hain"
        assert detect_language(text) == "ur"

    def test_single_urdu_keyword(self):
        """Only one Urdu keyword is not enough — should return English."""
        text = "The pani level is rising"
        assert detect_language(text) == "en"


# ---------------------------------------------------------------------------
# Location Extraction
# ---------------------------------------------------------------------------

class TestLocationExtraction:
    def test_sector_code_g10(self):
        """Sector code G-10 should be extracted."""
        text = "Flooding in G-10 sector is very bad"
        assert extract_location(text) == "G-10"

    def test_sector_code_f6(self):
        """Sector code F-6 should be extracted."""
        text = "Heavy rain causing flash flood in F-6 sector"
        assert extract_location(text) == "F-6"

    def test_named_location_shahrah(self):
        """Named location Shahrah-e-Faisal should be extracted."""
        text = "Shahrah-e-Faisal completely jammed after truck accident"
        assert extract_location(text) == "Shahrah-e-Faisal"

    def test_named_location_karachi(self):
        """Named city Karachi should be extracted."""
        text = "Karachi mein shadeed garmi, 47 degrees record"
        assert extract_location(text) == "Karachi"

    def test_no_location(self):
        """Text without any recognised location returns None."""
        text = "It is raining very hard here"
        assert extract_location(text) is None

    def test_named_location_blue_area(self):
        """Named location Blue Area should be extracted."""
        text = "Blue Area mein garmi se log behosh ho rahe hain"
        assert extract_location(text) == "Blue Area"


# ---------------------------------------------------------------------------
# Severity Tagging
# ---------------------------------------------------------------------------

class TestSeverityTagging:
    def test_high_severity_flash_flood(self):
        text = "Flash flood happening at George Town"
        assert tag_severity(text) == "high"

    def test_high_severity_accident(self):
        text = "Major accident on the highway, people injured"
        assert tag_severity(text) == "high"

    def test_medium_severity_blocked(self):
        text = "Road is completely blocked and jammed"
        assert tag_severity(text) == "medium"

    def test_low_severity_rain(self):
        text = "Light rain in the city today"
        assert tag_severity(text) == "low"

    def test_default_low_severity(self):
        text = "Some general news from the area"
        assert tag_severity(text) == "low"


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------

class TestKeywordExtraction:
    def test_flood_keywords(self):
        text = "Flash flood with heavy rain causing waterlogging"
        keywords = extract_keywords(text)
        assert "flood" in keywords
        assert "rain" in keywords

    def test_heatwave_keywords(self):
        text = "Extreme heat at 48 degrees, people collapsing"
        keywords = extract_keywords(text)
        assert "heat" in keywords
        assert "collapsing" in keywords


# ---------------------------------------------------------------------------
# Signal Processing Pipeline
# ---------------------------------------------------------------------------

class TestProcessSignal:
    def test_urdu_flood_signal(self):
        """Full pipeline test with Urdu flood input."""
        raw = RawSignalInput(
            source="social",
            text="G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
        )
        signal = process_signal(raw)
        assert signal.language == "ur"
        assert signal.location == "G-10"
        assert signal.severity_hint == "high"
        assert signal.source == "social"
        assert "pani" in signal.keywords

    def test_english_heatwave_signal(self):
        """Full pipeline test with English heatwave input."""
        raw = RawSignalInput(
            source="social",
            text="It's 48 degrees in Jacobabad, people collapsing on the street",
        )
        signal = process_signal(raw)
        assert signal.language == "en"
        assert signal.location == "Jacobabad"
        assert signal.severity_hint == "high"  # "collapsing" triggers high
        assert "degrees" in signal.keywords or "collapsing" in signal.keywords

    def test_english_blockage_signal(self):
        """Full pipeline test with English blockage input."""
        raw = RawSignalInput(
            source="traffic",
            text="Shahrah-e-Faisal completely jammed after truck accident",
        )
        signal = process_signal(raw)
        assert signal.language == "en"
        assert signal.location == "Shahrah-e-Faisal"
        assert signal.source == "traffic"

    def test_metadata_geo_fallback(self):
        """If no location in text, use metadata geo."""
        raw = RawSignalInput(
            source="social",
            text="Very heavy rain here, roads flooded",
            metadata={"geo": "F-7"},
        )
        signal = process_signal(raw)
        assert signal.location == "F-7"
