"""Live signal scanner – real Pakistani weather + news.

Sources (no API key needed):
  1. wttr.in  – real-time temperature for Pakistani cities
  2. Dawn / ARY News RSS  – crisis headlines from Pakistani press
  3. Season-aware fallback  – realistic signals when live sources fail
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List

from models.signal import RawSignalInput

# ---------------------------------------------------------------------------
# Cities monitored for heatwave (wttr.in name, display name)
# ---------------------------------------------------------------------------
_HEAT_CITIES = [
    ("Jacobabad",  "Jacobabad, Sindh"),
    ("Sukkur",     "Sukkur, Sindh"),
    ("Multan",     "Multan, Punjab"),
    ("Larkana",    "Larkana, Sindh"),
    ("Karachi",    "Karachi"),
]

_HEATWAVE_C = 40   # feels-like °C threshold to raise a heatwave signal
_CRITICAL_C = 48   # feels-like °C that upgrades severity to critical

# ---------------------------------------------------------------------------
# RSS feeds
# ---------------------------------------------------------------------------
_RSS_FEEDS = [
    "https://www.dawn.com/feeds/home",
    "https://arynews.tv/feed/",
]

_CRISIS_KW = [
    "flood", "heatwave", "heat wave", "heat stroke", "heatstroke",
    "earthquake", "landslide", "storm", "cyclone", "fire", "explosion",
    "accident", "collapse", "rain", "monsoon", "drought", "power outage",
    "blocked", "rescue", "emergency", "casualt", "dead", "injured",
]

_PAK_KW = [
    "pakistan", "karachi", "lahore", "islamabad", "rawalpindi", "peshawar",
    "quetta", "multan", "sindh", "punjab", "kpk", "balochistan",
    "jacobabad", "sukkur", "hyderabad", "faisalabad", "murree",
    "naran", "gilgit", "hunza", "larkana", "bahawalpur",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 6) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CIRO/1.0 crisis-intelligence"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------------------
# Weather scanner
# ---------------------------------------------------------------------------

def _scan_weather() -> List[RawSignalInput]:
    signals: List[RawSignalInput] = []
    for wttr_name, display_name in _HEAT_CITIES:
        try:
            raw = _http_get(
                f"https://wttr.in/{urllib.parse.quote(wttr_name)}?format=j1",
                timeout=3,
            )
            data = json.loads(raw)
            cond = data["current_condition"][0]
            temp_c   = int(cond.get("temp_C", 0))
            feels_c  = int(cond.get("FeelsLikeC", 0))
            desc     = cond.get("weatherDesc", [{}])[0].get("value", "")
            humidity = cond.get("humidity", "?")

            if feels_c >= _HEATWAVE_C or temp_c >= 40:
                severity = "critical" if (feels_c >= _CRITICAL_C or temp_c >= 48) else "high"
                text = (
                    f"Extreme heatwave in {display_name}: temperature {temp_c}°C, "
                    f"feels like {feels_c}°C, humidity {humidity}%. "
                    f"Condition: {desc}. Risk of heatstroke — outdoor activities dangerous."
                )
                signals.append(RawSignalInput(
                    source="weather",
                    text=text,
                    metadata={
                        "geo": display_name,
                        "severity": severity,
                        "temp_c": temp_c,
                        "feels_c": feels_c,
                        "live": True,
                    },
                ))
        except Exception:
            pass
    return signals


# ---------------------------------------------------------------------------
# RSS news scanner
# ---------------------------------------------------------------------------

def _scan_rss() -> List[RawSignalInput]:
    signals: List[RawSignalInput] = []
    for feed_url in _RSS_FEEDS:
        try:
            xml_bytes = _http_get(feed_url, timeout=8)
            root = ET.fromstring(xml_bytes)
            for item in root.findall(".//item")[:25]:
                title = item.findtext("title") or ""
                desc  = item.findtext("description") or ""
                blob  = f"{title} {desc}".lower()

                if any(kw in blob for kw in _CRISIS_KW) and any(kw in blob for kw in _PAK_KW):
                    combined = f"{title}. {desc[:300].strip()}" if desc else title
                    signals.append(RawSignalInput(
                        source="social",
                        text=combined[:600],
                        metadata={"source": feed_url, "headline": title, "live": True},
                    ))
                if len(signals) >= 3:
                    break
        except Exception:
            pass
        if len(signals) >= 3:
            break
    return signals


# ---------------------------------------------------------------------------
# Season-aware fallback (always returns something useful for demos)
# ---------------------------------------------------------------------------

def _fallback_signals() -> List[RawSignalInput]:
    month = datetime.now(timezone.utc).month

    if 4 <= month <= 6:   # Pre-monsoon: dry heatwave peak
        return [
            RawSignalInput(
                source="weather",
                text=(
                    "Severe heatwave alert: Jacobabad temperature 50°C, feels like 55°C. "
                    "Pakistan Meteorological Department issues red warning. Heatstroke "
                    "cases admitted to Civil Hospital Jacobabad. All schools closed. "
                    "Sindh government activates emergency cooling centres."
                ),
                metadata={"geo": "Jacobabad, Sindh", "severity": "critical"},
            ),
            RawSignalInput(
                source="weather",
                text=(
                    "Extreme heat warning for South Punjab: Multan 47°C, Bahawalpur 46°C, "
                    "Rahim Yar Khan 45°C. Power outages worsening conditions. Crop damage "
                    "reported. Labourers collapsing on fields."
                ),
                metadata={"geo": "Multan, Punjab", "severity": "high"},
            ),
        ]
    elif 7 <= month <= 9:  # Monsoon: flood / storm season
        return [
            RawSignalInput(
                source="weather",
                text=(
                    "Flash flood warning: heavy monsoon rains in Karachi — NDMA issues "
                    "red alert. Lyari River overflowing. Orangi Town and Baldia Town "
                    "flooded. Rescue teams deployed."
                ),
                metadata={"geo": "Karachi", "severity": "critical"},
            ),
            RawSignalInput(
                source="social",
                text=(
                    "Nullah Leh Rawalpindi overflowing after 200mm rain in 3 hours. "
                    "Saddar area flooded. Kashmir Highway blocked near Faizabad. "
                    "PDMA Rawalpindi requests army assistance."
                ),
                metadata={"geo": "Rawalpindi", "severity": "high"},
            ),
        ]
    elif month in (10, 11):  # Autumn: smog / fog season
        return [
            RawSignalInput(
                source="weather",
                text=(
                    "Severe smog alert for Lahore — AQI 450+ (Hazardous). Visibility "
                    "under 50 metres on GT Road and Motorway M-2. Schools closed. "
                    "EPA issues health emergency for children and elderly."
                ),
                metadata={"geo": "Lahore", "severity": "high"},
            ),
        ]
    else:  # Winter: dense fog
        return [
            RawSignalInput(
                source="weather",
                text=(
                    "Dense fog advisory: GT Road Lahore to Islamabad — zero visibility. "
                    "Multiple pile-ups reported near Gujranwala. Motorway M-2 closed. "
                    "Rescue 1122 teams deployed."
                ),
                metadata={"geo": "Lahore", "severity": "high"},
            ),
        ]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scan_live_signals(max_signals: int = 3) -> List[RawSignalInput]:
    """Return up to *max_signals* live signals, weather-first.

    Priority: live weather > live RSS > season-aware fallback.
    Always returns at least one signal.
    """
    weather = _scan_weather()
    news    = _scan_rss()
    combined = weather + news

    if not combined:
        combined = _fallback_signals()

    # Pick the most severe first
    def _sev_rank(s: RawSignalInput) -> int:
        sev = (s.metadata or {}).get("severity", "low")
        return {"critical": 3, "high": 2, "medium": 1}.get(str(sev), 0)

    combined.sort(key=_sev_rank, reverse=True)
    return combined[:max_signals]
