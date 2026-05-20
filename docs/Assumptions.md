# CIRO — Assumptions & Boundaries

What is **real engineering** vs **scoped demo behaviour** for reviewers and new contributors.

---

## Simulation boundaries

- **No persistence.** Signals, events, tickets, alerts, world state, and trace history live in process memory. Restarting Uvicorn or calling `/simulate/reset` clears everything.
- **Single-tenant, single-process.** No auth, no rate limits, one worker — designed for demo and pytest, not production load.
- **Pakistani urban scope.** Location gazetteer covers sectors and named roads (G-10, I-9, Shahrah-e-Faisal, Jacobabad, Karachi, …). Unknown locations fall back to `"Unknown"`.
- **Bilingual, bounded.** Urdu (Arabic script) and English detection; romanised Urdu keywords (`pani`, `aag`) via gazetteer, not a full NLP stack.

---

## Mock vs live data

| Source | Behaviour |
|--------|-----------|
| `/mock/social`, `/mock/weather`, `/mock/traffic` | Fully simulated JSON |
| `/ingest/auto` | Pulls from mock files; caps signals; optional `location_filter` |
| `/pipeline/auto` | **Partially live** — wttr.in temperatures + Dawn/ARY RSS; season fallback if offline |
| `/maps/crisis-overlay` | Pre-authored GeoJSON in `backend/data/` |
| Tickets & alerts | In-memory only; not sent to real dispatch systems |

Population figures and congestion deltas are **deterministic functions** of severity/location, not census or live traffic APIs.

---

## LLM assumptions

| Path | When used |
|------|-----------|
| **Groq** | `POST /reason/analyse` when `GROQ_API_KEY` is set |
| **Fallback cache** | Always available per `(crisis_type, severity)` |
| **Gemini / ADK** | Antigravity agent workflow (`adk web agents`) |

Without any API keys, all **scripted demo scenarios** still complete with cached reasoning. Token usage is not optimised for cost.

---

## Antigravity / ADK assumptions

- FastAPI routes are the **source of truth** for agent behaviour; ADK tools are thin HTTP wrappers.
- The workflow graph in Antigravity should match the five-step order: ingest → detect → reason → plan → simulate.
- `TraceStore` mirrors execution for mobile/web; Antigravity’s own trace tab may differ slightly in timing.

---

## API limitations

- Trace history capped at **10 runs**.
- `/simulate/tickets` and `/simulate/alerts` return **bare arrays** (clients must not assume a wrapper object).
- `/simulate/alerts/stream` is infinite unless `?once=true` is passed.
- Endpoints target **&lt; 500 ms** under single-user demo load; not load-tested.

---

## Mobile app assumptions

- Primary demo target: **Android** (emulator `10.0.2.2:8000`, physical device via LAN IP).
- Server URL stored in `SharedPreferences`; no automatic cloud discovery.
- Map screen uses backend GeoJSON overlays, not live Google Maps SDK tiles in-app.
- Alert polling interval: **2 seconds** on `/simulate/alerts/version`.

---

## Web dashboard assumptions

- Served as static files from FastAPI `/web` mount.
- Signal feed polls `/mock/social` on an interval; pipeline triggered manually or from UI.
- SSE preferred for alerts; falls back to version polling on connection error.

---

## What is genuinely real

- FastAPI + Pydantic pipeline and **139 automated tests**
- Bilingual normalisation and detection heuristics on real input text
- Groq reasoning when configured
- ADK SequentialAgent calling the same endpoints as production clients
- Flutter UI driven by live API responses (not hard-coded demo screens)
- Optional live weather/RSS scanner for `/pipeline/auto`

---

## Known demo caveats

- Internet loss: reasoning cache + mock overlays keep the five scripted scenarios working.
- `/trace/latest` may briefly show the previous run mid-pipeline; wait for completion before demoing trace.
- Timestamps are UTC; UI does not convert to PKT.
- `POST /pipeline/run` clears the ingest buffer so each one-shot run is isolated.
