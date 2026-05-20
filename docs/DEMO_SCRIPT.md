# CIRO Demo Script (3–5 minutes)

Use this script for the hackathon video or live judging. Assumes backend on `http://localhost:8000` and Flutter on a device/emulator.

---

## Pre-flight (30 s)

1. Start backend: `start_server.bat` or `uvicorn main:app --host 0.0.0.0 --port 8000` from `backend/`.
2. Open **web:** http://localhost:8000/web/index.html
3. Launch **Flutter** app; confirm green/online on Home (or set server URL to your LAN IP).
4. Optional: `python backend/scripts/qa_report.py` — all scenarios should show `"pass": true`.

---

## Act 1 — The problem (30 s)

> “Pakistani cities face floods, heatwaves, and gridlock — but response systems don’t connect social signals, weather, and traffic into one decision loop.”

Show idle web dashboard: empty crisis panel, signal feed waiting.

---

## Act 2 — Urdu flood, end-to-end (90 s)

**Web**

1. Click **TRIGGER PIPELINE** (or POST the Urdu G-10 scenario).
2. Narrate as agent cards turn **RUNNING → COMPLETE** (5 steps).
3. Point to **Crisis Detection:** `FLOOD`, confidence ≥ 0.70, severity **high/critical**, location **G-10**.
4. Expand **Agent Reasoning Trace** — show ingest → detect → reason → plan → simulate.
5. Show **Outcome Snapshot:** congestion reduced, alerts, tickets.
6. Scroll to **Live Map** — crisis pin, affected area, alternate route.

**Mobile (parallel or cut)**

1. Home → run same pipeline from FAB / scenario input.
2. **Crisis** tab — new history card with severity badge.
3. **Alerts** — badge increments; open to see dispatched alert + ticket.
4. **Trace** — same 5-step chain with timings.

**Talking point**

> “One API call runs five agents. The same endpoints are Antigravity ADK tools — we’re not hand-wiring glue code in the demo.”

---

## Act 3 — Real-time alerts (45 s)

1. Run a second scenario (e.g. fire: `Fire broke out in I-9 industrial area, smoke everywhere`).
2. Without refreshing manually, show **Alerts** updating on mobile within ~2 seconds (version polling).
3. On web, mention SSE on `/simulate/alerts/stream` with poll fallback.

---

## Act 4 — Multi-source & live scan (60 s)

**Buffered corroboration**

1. `POST /ingest/auto` with location `G-10` (Swagger or curl) then `POST /detect/crisis`.
2. Or run pipeline after auto-ingest — show **critical** confidence when weather + traffic align.

**Live scanner (optional, needs network)**

1. `POST /pipeline/auto` — explain wttr.in + Dawn/ARY RSS picking a real headline or heat signal.
2. Show resulting crisis type on map overlay.

---

## Act 5 — Low confidence contrast (30 s)

Input: `some news from somewhere today`

- Severity **low**, few or zero actions, no critical alerts.
- Reinforces the scoring system isn’t always firing alarms.

---

## Act 6 — Reset & Antigravity (30 s)

1. Click **Reset System** on web.
2. Briefly show `backend/agents/ciro_pipeline.py` or Antigravity ADK UI (`adk web agents`) if available.
3. Close with team + repo link.

---

## Backup if LLM/network fails

- Reasoning uses **cached analyses** for all scripted scenarios — pipeline still completes.
- Maps use **file-backed GeoJSON** — no Maps API quota needed for overlay demo.
- Say: “Production would use live Gemini via Antigravity; hackathon build degrades gracefully.”

---

## Quick reference payloads

| Label | `POST /pipeline/run` body |
|-------|---------------------------|
| Urdu flood | `{"source":"social","text":"G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"}` |
| Heatwave | `{"source":"social","text":"48 degrees in Jacobabad, people collapsing on the street"}` |
| Blockage | `{"source":"traffic","text":"Shahrah-e-Faisal completely jammed after truck accident"}` |
| Fire | `{"source":"social","text":"Fire broke out in I-9 industrial area, smoke everywhere"}` |
| Low signal | `{"source":"social","text":"some news from somewhere today"}` |
