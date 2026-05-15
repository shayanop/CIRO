# CIRO – Assumptions & Boundaries

This document lists the simulation boundaries, mock-data assumptions, and API limitations that the CIRO hackathon build operates under. It exists so reviewers know what is **real engineering** vs. **scoped-down demo behaviour**.

---

## Simulation Boundaries

- **No real signal ingestion.** Social, weather, and traffic feeds are simulated by `/mock/social`, `/mock/weather`, `/mock/traffic`. None of these reach external services.
- **No persistence.** All state (signals, events, tickets, alerts, world state, trace store) lives in process memory. Restarting the FastAPI server resets the system. `/simulate/reset` performs an in-memory reset.
- **Single-tenant, single-process.** No user accounts, no auth, one Uvicorn worker. Concurrency is not designed for.
- **Pakistani urban scope only.** Locations and the bilingual gazetteer are hard-coded for Pakistani sectors (G-10, Shahrah-e-Faisal, Constitution Avenue, etc.). The system will not recognise locations outside this list.
- **Bilingual but bounded.** Language detection covers Urdu (Arabic script) and English. Urdu romanised in Latin script (`pani`, `garmi`) is handled via the keyword gazetteer, not via a real NLP model.

---

## Mock Data Assumptions

- **Five demo scenarios are first-class.** The reasoning agent has a cached `CrisisAnalysis` for each of: Urdu flood (G-10), English heatwave, multi-source flood, road blockage, low-confidence single-signal. Other inputs may produce degraded analyses.
- **Maps.** Google Maps responses are pre-saved GeoJSON files served from `/maps/crisis-overlay`. We do not hit the live Maps API during the demo (quota + offline-recording safety).
- **Weather/traffic baselines.** Mock endpoints return a fixed baseline shape; "anomalies" are flipped on by demo control endpoints rather than generated stochastically.
- **Affected-population numbers** are deterministic functions of severity and location, not real census data.
- **Tickets and alerts** are pure in-memory objects. They are not sent to any real dispatch system.

---

## LLM / Gemini Assumptions

- Gemini 1.5 Pro is invoked **through Antigravity**, not from Python directly. If Antigravity is unreachable, the Reasoning agent falls back to the cached response keyed by `(crisis_type, severity)`.
- Gemini is **only** used by the Reasoning agent. The other four agents are deterministic.
- Token cost is not optimised — prompts include the full signal text and event JSON.
- Schema enforcement on the LLM output is done by Antigravity's structured-output validator. We do not retry malformed outputs; we fall back to cache.

---

## Antigravity Assumptions

- The agent graph is configured in Antigravity once (Day 2) and is not regenerated from code. If the underlying schemas change, the graph must be re-saved manually.
- Each edge expects strictly-typed JSON. Adding a non-optional field to a schema is a breaking change to the edge.
- Antigravity's trace tab is the **canonical** trace. Our `TraceStore` is a mirror used so the mobile/web UIs do not need to call Antigravity directly.

---

## API Limitations

- All endpoints respond < 500 ms under demo load (single user, hot-cached scenarios). They are not load-tested.
- No rate limiting, no API keys on the FastAPI side.
- Trace history is capped at the **last 10 runs** in memory.
- `/simulate/state` returns the full world dict; it is not paginated.

---

## Mobile App Assumptions

- The Flutter app targets **Android** as the primary demo platform. iOS builds are not validated.
- The app talks to a backend at `http://<demo-host>:8000`. There is no service-discovery or production base-URL switching.
- The Map screen renders crisis overlays from `/maps/crisis-overlay` — it does not consume the live Google Maps SDK during the demo.

---

## What is NOT Mocked (genuinely real)

To make the engineering trade-off explicit, these parts are real, not simulated:

- The five-agent **orchestration in Antigravity** is real and produces real traces.
- The **Gemini 1.5 Pro** reasoning call is real (with cache fallback).
- The **FastAPI backend, Pydantic schemas, and trace store** are real Python code.
- The **Flutter app screens** are real, render real backend data, and handle real state transitions.
- The **bilingual signal normalisation** (language detect + keyword extraction + location resolution) runs real logic on real input text.

---

## Known Demo Caveats

- If the demo host loses internet, the Reasoning agent's cached fallback covers all five scripted scenarios, so the pipeline still completes.
- The Antigravity trace tab and our `TraceStore` are eventually consistent — there is a small window during a run where `/trace/latest` may return the previous run. Demo timing accounts for this.
- All timestamps are UTC. The UI does not localise to PKT.
