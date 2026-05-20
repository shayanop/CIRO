# CIRO — System Architecture

## Overview

CIRO (Crisis Intelligence & Response Orchestrator) detects urban crises in Pakistani cities and produces coordinated response plans through a **five-agent sequential pipeline**. A single FastAPI process exposes each agent as REST endpoints; clients include the **web dashboard**, **Flutter app**, and **Google ADK SequentialAgent** (`backend/agents/ciro_pipeline.py`).

Data flows top-down: raw signal → `SignalBatch` → `CrisisEvent` → `CrisisAnalysis` → `ActionPlan` → `SimulationResult`, with every step logged to `TraceStore` and alert changes broadcast to UIs.

---

## The five layers

### 1. Signal Ingestion

| | |
|---|---|
| **Router** | `backend/routers/ingest.py` |
| **Input** | `RawSignalInput` (social / weather / traffic text or JSON) |
| **Output** | `SignalBatch` |

Responsibilities: language detection (Urdu script vs English), bilingual keyword extraction, location resolution (G-10, Shahrah-e-Faisal, Jacobabad, …), severity hints, engagement/metadata passthrough, in-memory signal buffer.

Special endpoints:

- `POST /ingest/auto` — mock weather + traffic corroboration (capped, location-aware)
- `POST /ingest/clear` — reset buffer

### 2. Event Detection

| | |
|---|---|
| **Router** | `backend/routers/detect.py` |
| **Input** | `SignalBatch` |
| **Output** | `CrisisEvent` |

Responsibilities: classify among **8 crisis types**, compute confidence from keyword density, cross-source corroboration, traffic anomaly, engagement bonus, strong-evidence and location-anchor bonuses, optional escalation from prior events. Map confidence to severity via `confidence_to_severity` (0.75 / 0.55 / 0.35 thresholds).

### 3. Reasoning & Analysis

| | |
|---|---|
| **Router** | `backend/routers/reason.py` |
| **Input** | `CrisisEvent` |
| **Output** | `CrisisAnalysis` |

Responsibilities: structured impact bullets, population estimate, infrastructure risk, urgency, summary. Primary path: **Groq** (`GROQ_API_KEY`). Fallback: deterministic cache per `(crisis_type, severity)` so demos never block.

### 4. Action Planning

| | |
|---|---|
| **Router** | `backend/routers/plan.py` |
| **Input** | `CrisisEvent` + `CrisisAnalysis` |
| **Output** | `ActionPlan` |

Responsibilities: map `(crisis_type, severity)` to executable actions (`reroute_traffic`, `dispatch_rescue_boats`, `send_alert`, `open_relief_camp`, …).

### 5. Simulation

| | |
|---|---|
| **Router** | `backend/routers/simulate.py` |
| **Input** | `ActionPlan` |
| **Output** | `SimulationResult` |

Responsibilities: apply actions to in-memory world state, create `EmergencyTicket` and `CiroAlert` records, compute congestion/ETA metrics, notify **`alert_broadcast`** (version counter + SSE).

---

## Orchestration paths

```
┌─────────────────────────────────────────────────────────────┐
│                     POST /pipeline/run                       │
│  (ingest → detect → reason → plan → simulate → complete_run) │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     POST /pipeline/auto                      │
│  live_scanner → pick signal → pipeline/run                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              ADK SequentialAgent (ciro_pipeline.py)          │
│  tool: ingest → detect → reason → plan → simulate            │
│  each tool = httpx POST to same FastAPI routes               │
└─────────────────────────────────────────────────────────────┘
```

---

## Real-time alert broadcast

`backend/services/alert_broadcast.py` maintains a monotonic **version** incremented whenever tickets or alerts change.

| Consumer | Mechanism |
|----------|-----------|
| Web | `EventSource` → `/simulate/alerts/stream`; fallback poll `/simulate/alerts/version` every 2s |
| Flutter | Poll `/simulate/alerts/version` every 2s; refresh tickets/alerts on change |

---

## Trace system

`backend/services/trace_store.py` stores per-run steps (agent name, step id, input/output JSON, duration).  

| Endpoint | Use |
|----------|-----|
| `GET /trace/latest` | Full step list for debugging and web trace panel |
| `GET /trace/history` | Last 10 runs with enriched crisis summaries for mobile Crisis feed |

---

## Maps layer

`backend/routers/maps.py` serves **file-backed GeoJSON** from `backend/data/*_overlay.json` — no live Maps API required for overlays. Optional `GET /maps/static-map` builds a Google Static Maps URL when `GOOGLE_MAPS_API_KEY` is set.

---

## Live signal scanner

`backend/services/live_scanner.py` (used by `/pipeline/auto`):

1. **wttr.in** — real temperatures for Pakistani cities (heatwave thresholds)
2. **Dawn / ARY RSS** — crisis-related headlines
3. **Season-aware fallback** — when network sources fail

This is partial real-world ingestion; detection/plan/simulation remain the same pipeline.

---

## Component ownership

| Surface | Tech | Primary owner |
|---------|------|----------------|
| FastAPI backend | Python, Pydantic | Anas / Arshman / Hasnain |
| ADK agents | `google-adk`, Gemini tools | Anas |
| Reasoning LLM | Groq + cache | Arshman |
| Trace + structlog | Python services | Shayan |
| Web dashboard | HTML/CSS/JS, Leaflet | Hasnain |
| Flutter app | Dart, Provider | Saad |
| Docs & QA scripts | Markdown, pytest | Shayan / Anas |

---

## Non-goals (hackathon scope)

- No database — in-memory state only; restart or `/simulate/reset` clears everything
- No authentication or multi-tenancy
- No production-scale load testing
- Social/weather/traffic mocks under `/mock/*`; live scanner is best-effort

---

## Related documents

- [`PIPELINE_CONTRACT.md`](PIPELINE_CONTRACT.md) — JSON schemas
- [`API_REFERENCE.md`](API_REFERENCE.md) — HTTP reference
- [`AgentDesign.md`](AgentDesign.md) — per-agent logic
- [`QA_METRICS.md`](QA_METRICS.md) — test and latency targets
