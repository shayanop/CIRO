# CIRO — Crisis Intelligence & Response Orchestrator

> Agentic AI for real-time urban crisis detection, reasoning, and coordinated response — built for the **Google Antigravity Hackathon** (Challenge 3).

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)]()
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=flat-square&logo=flutter&logoColor=white)]()

---

## What is CIRO?

Pakistani cities face recurring urban crises — flash floods in G-10, heatwaves in Jacobabad, blockages on Shahrah-e-Faisal, fires in industrial sectors. Response is often fragmented and reactive.

**CIRO** runs a **5-agent pipeline** that:

1. **Ingests** multi-source signals (social, weather, traffic — mock + optional live scan)
2. **Detects** crisis type and severity with confidence scoring
3. **Reasons** over impact, population, and urgency (Groq LLM with deterministic fallback cache)
4. **Plans** coordinated response actions
5. **Simulates** execution and surfaces before/after outcomes, tickets, and alerts

Clients talk to a single **FastAPI** backend. The same endpoints are registered as **Google ADK tools** in `backend/agents/ciro_pipeline.py` for Antigravity orchestration.

---

## Repository layout

```
CIRO/
├── backend/                 # FastAPI API, agents, tests, mock data
│   ├── main.py              # App entry — mounts routers + /web static
│   ├── routers/             # Per-agent HTTP handlers
│   ├── models/              # Pydantic schemas (signal, simulation)
│   ├── services/            # Trace store, alert broadcast, live scanner
│   ├── agents/              # Google ADK SequentialAgent (ciro_pipeline.py)
│   ├── data/                # GeoJSON overlays, mock JSON
│   ├── tests/               # 139 pytest tests
│   └── scripts/qa_report.py # Demo scenario matrix (JSON)
├── web/                     # Operations dashboard (served at /web)
├── frontend/ciro_app/       # Flutter mobile app (5 screens)
├── docs/                    # Architecture, API, pipeline contract, QA
├── Plans/                   # Team sprint plans
├── .env.example             # Environment template (copy to backend/.env)
└── start_server.bat         # Windows: uvicorn on 0.0.0.0:8000
```

---

## Quick start

### 1. Backend

```bash
git clone https://github.com/shayanop/CIRO.git
cd CIRO/backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env   # optional: GROQ_API_KEY, GEMINI_API_KEY, maps key
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/web/index.html | Web dashboard |
| http://localhost:8000/health | Health check |

**Windows shortcut:** run `start_server.bat` from the repo root (prints your LAN IP for the Flutter app).

### 2. Flutter app

```bash
cd frontend/ciro_app
flutter pub get
flutter run
```

- **Android emulator** default backend: `http://10.0.2.2:8000`
- **Physical device:** set your PC’s Wi‑Fi IP in the app (same network as the backend)
- Override URL anytime via in-app server settings (`SharedPreferences`)

### 3. Run tests & QA matrix

```bash
cd backend
python -m pytest -q
python scripts/qa_report.py
```

---

## Architecture (high level)

```
                    ┌─────────────────────────────────────┐
                    │  Clients: Web / Flutter / ADK CLI   │
                    └──────────────────┬──────────────────┘
                                       │ REST
                    ┌──────────────────▼──────────────────┐
                    │         FastAPI (backend/main.py)    │
                    ├──────────┬──────────┬──────────┬─────┤
                    │ Ingest   │ Detect   │ Reason   │ ... │
                    └────┬─────┴────┬─────┴────┬─────┴─────┘
                         │          │          │
              SignalBatch → CrisisEvent → CrisisAnalysis → ActionPlan → SimulationResult
                         │                              │
                         └──────── TraceStore ──────────┘
                                    │
                         Alert broadcast (SSE + version poll)
```

**One-shot orchestration:** `POST /pipeline/run` chains all five agents and completes the trace run.

**Live mode:** `POST /pipeline/auto` uses `services/live_scanner.py` (wttr.in + Pakistani RSS) to pick a signal, then runs the pipeline.

Details: [`docs/Architecture.md`](docs/Architecture.md) · [`docs/PIPELINE_CONTRACT.md`](docs/PIPELINE_CONTRACT.md)

---

## Technology stack

| Layer | Stack |
|-------|--------|
| API | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| Reasoning | Groq (`llama-3.3-70b-versatile`) + per-scenario fallback cache |
| Orchestration (hackathon) | Google ADK `SequentialAgent` → FastAPI tools |
| Maps | File-backed GeoJSON overlays + optional Google Static Maps URL |
| Logging / trace | structlog + in-memory `TraceStore` |
| Web UI | Vanilla JS, Leaflet/OSM, SSE alert stream |
| Mobile | Flutter 3, Provider, `http` client |
| Tests | pytest (139 tests), `scripts/qa_report.py` |

---

## The five agents

| # | Agent | Endpoint | Output |
|---|--------|----------|--------|
| 1 | Signal Ingestion | `POST /ingest/signal` | `SignalBatch` |
| 2 | Event Detection | `POST /detect/crisis` | `CrisisEvent` |
| 3 | Reasoning & Analysis | `POST /reason/analyse` | `CrisisAnalysis` |
| 4 | Action Planning | `POST /plan/actions` | `ActionPlan` |
| 5 | Simulation Engine | `POST /simulate/execute` | `SimulationResult` |

**Crisis types (8):** `flood`, `heatwave`, `blockage`, `accident`, `fire`, `earthquake`, `storm`, `infrastructure`

**Severity ladder** (`confidence_to_severity`):

| Confidence ≥ | Severity |
|--------------|----------|
| 0.75 | critical |
| 0.55 | high |
| 0.35 | medium |
| &lt; 0.35 | low |

Detection uses keyword clustering, cross-source corroboration, engagement/location bonuses, and optional escalation when prior events exist in the buffer.

---

## API overview

Full reference: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)

### Pipeline & ingest

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pipeline/run` | Full 5-agent run from one raw signal |
| `POST` | `/pipeline/auto` | Live scan → highest-severity signal → pipeline |
| `POST` | `/ingest/signal` | Normalise one signal into batch |
| `POST` | `/ingest/auto` | Auto-ingest mock weather + traffic (capped, location-aware) |
| `POST` | `/ingest/clear` | Clear signal buffer |

### Simulation & real-time alerts

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/simulate/execute` | Execute action plan |
| `POST` | `/simulate/reset` | Reset world state |
| `GET` | `/simulate/state` | Current mock system state |
| `GET` | `/simulate/tickets` | Emergency tickets (JSON array) |
| `GET` | `/simulate/alerts` | Sent alerts (JSON array) |
| `GET` | `/simulate/alerts/version` | Version + counts for polling |
| `GET` | `/simulate/alerts/stream` | SSE stream (`?once=true` for single event) |
| `PATCH` | `/simulate/tickets/{id}/status` | Update ticket (`{"status":"..."}` or query param) |

### Maps, outcome, trace, mocks

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/maps/crisis-overlay` | GeoJSON pin, polygon, routes |
| `GET` | `/maps/static-map` | Google Static Maps URL |
| `GET` | `/maps/routes` | Alternate route library |
| `GET` | `/outcome/summary` | Before/after metrics |
| `GET` | `/trace/latest` | Full steps for latest run |
| `GET` | `/trace/history` | Last 10 runs (enriched summaries + steps) |
| `GET` | `/mock/social` | Random mock social signal |
| `GET` | `/mock/weather` | Mock weather JSON |
| `GET` | `/mock/traffic` | Mock traffic JSON |
| `GET` | `/health` | Service health |

---

## Web dashboard

Served at **`/web/index.html`** when the backend is running.

| Section | Behaviour |
|---------|-----------|
| Live Signal Feed | Polls `/mock/social`; shows engagement when present |
| Agent Pipeline | Animated IDLE → RUNNING → COMPLETE per agent |
| Crisis Detection | Confidence gauge, severity, explanation |
| Simulation Log | Tickets and alerts |
| Outcome Snapshot | Congestion, ETA, alerts, tickets |
| Live Map | Leaflet + crisis GeoJSON overlay |
| Agent Trace | Expandable stepper from `/trace/latest` |
| Controls | **Trigger Pipeline** (`POST /pipeline/run`), **Reset** |

**Real-time alerts:** `EventSource` on `/simulate/alerts/stream` with 2s polling fallback via `/simulate/alerts/version`.

---

## Flutter app (`frontend/ciro_app`)

Five bottom-nav screens:

| Screen | Features |
|--------|----------|
| **Home** | Before/after command centre, run pipeline FAB, outcome summary |
| **Crisis** | Trace history feed with severity-coded cards |
| **Map** | Crisis overlay, routes, run pipeline |
| **Alerts** | Tickets + alerts, badge on new dispatches |
| **Trace** | 5-step agent stepper with timings |

Polls **`/simulate/alerts/version` every 2s** and refreshes tickets/alerts when the version changes.

See [`frontend/ciro_app/README.md`](frontend/ciro_app/README.md).

---

## Google Antigravity / ADK

`backend/agents/ciro_pipeline.py` defines a **SequentialAgent** whose tools call the same FastAPI endpoints as the web and mobile clients.

```bash
cd backend
# Ensure BACKEND_URL=http://localhost:8000 in .env and server is running
adk web agents    # browser UI
adk run agents    # CLI
```

Set `GEMINI_API_KEY` / `GOOGLE_CLOUD_PROJECT` for ADK LLM steps; set `GROQ_API_KEY` for the Reasoning agent’s direct API path.

---

## Environment variables

Copy [`.env.example`](.env.example) to **`backend/.env`**:

```env
GROQ_API_KEY=              # Reasoning agent (optional — cache fallback)
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT_SECONDS=5

GEMINI_API_KEY=            # ADK / Antigravity
GOOGLE_CLOUD_PROJECT=
ANTIGRAVITY_PROJECT_ID=

GOOGLE_MAPS_API_KEY=       # Static map URLs only
BACKEND_URL=http://localhost:8000
```

Without API keys, demo scenarios still pass using the **reasoning fallback cache** and mock data.

---

## Demo scenarios

| # | Scenario | Sample input | Expected |
|---|----------|--------------|----------|
| 1 | Urdu flood G-10 | `G-10 mein pani bhar gaya hai, gaariyan phans gayi hain` | `flood`, confidence ≥ 0.70, high/critical |
| 2 | English heatwave | `48 degrees in Jacobabad, people collapsing` | `heatwave`, high/critical |
| 3 | Shahrah blockage | `Shahrah-e-Faisal completely jammed after truck accident` | `blockage`, high+ |
| 4 | Fire I-9 | `Fire broke out in I-9 industrial area, smoke everywhere` | `fire`, high, alerts |
| 5 | Low confidence | `some news from somewhere today` | `low`, no critical actions |
| 6 | Multi-source (buffer) | Social + weather + traffic via `/ingest/auto` | `critical`, confidence ≥ 0.85 |

Demo walkthrough: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)

---

## Quality metrics

| Metric | Value |
|--------|-------|
| Automated tests | **139** (`pytest` in `backend/`) |
| Typical test runtime | ~2 s |
| Full pipeline latency | &lt; 30 ms typical (in-process, cached reasoning) |
| QA script | `python backend/scripts/qa_report.py` |

See [`docs/QA_METRICS.md`](docs/QA_METRICS.md).

---

## Documentation index

| Document | Description |
|----------|-------------|
| [`docs/Architecture.md`](docs/Architecture.md) | Layers, data flow, component ownership |
| [`docs/AgentDesign.md`](docs/AgentDesign.md) | Per-agent schemas and decision logic |
| [`docs/PIPELINE_CONTRACT.md`](docs/PIPELINE_CONTRACT.md) | JSON contracts for pipeline I/O |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Endpoint reference with examples |
| [`docs/QA_METRICS.md`](docs/QA_METRICS.md) | Test counts, thresholds, alert mechanisms |
| [`docs/Assumptions.md`](docs/Assumptions.md) | Mock boundaries and demo caveats |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | 3–5 minute demo script |
| [`Plans/`](Plans/) | Team sprint plans (implementation + final sprint) |

---

## Team

| Name | Role |
|------|------|
| **Anas Bin Rashid** | Lead — ingestion, simulation, integration, Antigravity |
| **Hasnain Akhtar** | Detection, maps, web dashboard |
| **Arshman Khawar** | Reasoning, mocks, backend |
| **M Saad Mursaleen** | Flutter app & UX |
| **Shayan Ahmed** | Trace, docs, demo |

---

<p align="center">
  <b>CIRO — Crisis Intelligence & Response Orchestrator</b><br>
  Challenge 3 · Google Antigravity Hackathon
</p>
