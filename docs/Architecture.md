# CIRO – System Architecture

## Overview

CIRO (Crisis Intelligence & Response Orchestrator) is an agentic AI system that detects urban crises in Pakistani cities and produces coordinated response plans. It is composed of five specialised agents executed sequentially through **Google Antigravity**.

The system is split into five logical layers. Data flows top-down: a raw signal enters at the Ingestion layer and exits as a simulated outcome at the Simulation layer, with the full trace surfaced back to the user.

---

## The Five Layers

### 1. Signal Ingestion Layer
- **Owner agent**: Signal Ingestion Agent
- **Input**: Raw text/JSON from social feeds, weather APIs, traffic feeds (mock sources for the hackathon)
- **Responsibility**: Normalise heterogeneous input into a canonical `SignalBatch`. Detect language (Urdu/English), extract location tokens, tag a coarse severity hint.
- **Output**: `SignalBatch` (list of normalised `Signal` records with `source`, `text`, `language`, `location`, `severity_hint`, `timestamp`).

### 2. Event Detection Layer
- **Owner agent**: Event Detection Agent
- **Input**: `SignalBatch`
- **Responsibility**: Cluster signals by location and topic, score confidence using multi-source corroboration, classify the crisis type (Flood / Heatwave / Blockage / Accident) and severity (LOW → MEDIUM → HIGH → CRITICAL).
- **Output**: `CrisisEvent` (type, location, severity, confidence, contributing_signal_ids).

### 3. Reasoning & Analysis Layer
- **Owner agent**: Reasoning & Analysis Agent (Gemini 1.5 Pro via Antigravity)
- **Input**: `CrisisEvent`
- **Responsibility**: Produce structured reasoning: impact bullets, affected population estimate, infrastructure-at-risk list, urgency level, recommended response themes. Falls back to a cached response if the model call fails.
- **Output**: `CrisisAnalysis` (impact, affected_population, infrastructure_at_risk, urgency, summary).

### 4. Action Planning Layer
- **Owner agent**: Action Planning Agent
- **Input**: `CrisisAnalysis` + the originating `CrisisEvent`
- **Responsibility**: Map (crisis_type × severity) to a concrete list of executable actions (e.g. `reroute_traffic`, `dispatch_rescue_boats`, `send_flood_alert`, `open_relief_camp`). Each action has parameters resolved from the analysis.
- **Output**: `ActionPlan` (ordered list of `Action` records).

### 5. Simulation Layer
- **Owner agent**: Simulation Engine Agent
- **Input**: `ActionPlan`
- **Responsibility**: Apply each action to an in-memory mock world. Snapshot the world before and after. Create `EmergencyTicket` and `Alert` objects. Compute outcome metrics: congestion delta, ETA, alerts dispatched.
- **Output**: `SimulationResult` (before, after, tickets, alerts, metrics).

---

## End-to-End Data Flow

```
Raw signal (Urdu/English text or JSON)
        │
        ▼
[1] Signal Ingestion Agent   ──►  SignalBatch
        │
        ▼
[2] Event Detection Agent    ──►  CrisisEvent
        │
        ▼
[3] Reasoning Agent (Gemini) ──►  CrisisAnalysis
        │
        ▼
[4] Action Planning Agent    ──►  ActionPlan
        │
        ▼
[5] Simulation Agent         ──►  SimulationResult
        │
        ▼
   TraceStore ──► /trace/latest ──► Mobile + Web UIs
```

Every agent step is appended to a `TraceStore` keyed by `run_id`, so the full reasoning chain is queryable via REST after each run.

---

## Antigravity's Role

Antigravity is the **orchestration substrate** — CIRO does not chain agents manually in Python. Instead:

- Each FastAPI endpoint is registered as a **tool** inside Antigravity.
- Antigravity's **workflow editor** defines the agent graph (which agent feeds which, and the JSON schema of each edge).
- Antigravity invokes **Gemini 1.5 Pro** inside the Reasoning agent — the LLM call is not made directly from Python.
- Antigravity's **trace tab** is the source of truth for what each agent received and produced; our `TraceStore` mirrors this for the mobile app.
- **State passing** between agents uses Pydantic-validated JSON; Antigravity enforces the schema at each edge.

Why Antigravity rather than a hand-rolled orchestrator: it accounts for 25% of the hackathon score, gives us free per-step tracing, and lets the team iterate on the agent graph visually without code changes.

---

## Component Boundaries

| Surface | Tech | Owner |
|---|---|---|
| Backend API | FastAPI + Pydantic | Hasnain / Arshman |
| Agents | Antigravity workflow + registered FastAPI tools | Anas |
| AI reasoning | Gemini 1.5 Pro via Antigravity | Arshman |
| Trace store + logger | Python in-memory + structlog | Shayan |
| Web dashboard | Served at `/web` by FastAPI | Hasnain |
| Mobile app | Flutter 3 | Saad |

---

## Non-Goals (this hackathon)

- No persistence layer — all state is in-memory and reset by `/simulate/reset`.
- No real social/weather/traffic ingestion — endpoints under `/mock/*` return canned data.
- No authentication — single-tenant demo scope.
- No horizontal scaling — single FastAPI process.
