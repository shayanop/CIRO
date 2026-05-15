# 🚨 CIRO – Crisis Intelligence & Response Orchestrator

> **An Agentic AI System for real-time urban crisis detection, reasoning, and coordinated response — powered by Google Antigravity & Gemini.**

[![Google Antigravity Hackathon](https://img.shields.io/badge/Challenge%203-Google%20Antigravity%20Hackathon-blue?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)]()
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=flat-square&logo=flutter&logoColor=white)]()
[![Gemini](https://img.shields.io/badge/Gemini%201.5%20Pro-AI%20Reasoning-8E75B2?style=flat-square&logo=google&logoColor=white)]()

---

## 📖 Overview

Pakistan's cities face recurring urban crises — flash floods in G-10, heatwaves in Jacobabad, road blockages on Shahrah-e-Faisal, infrastructure failures on Constitution Avenue. Current response systems are fragmented and reactive.

**CIRO** solves this by orchestrating a **5-agent AI pipeline** that:
1. **Ingests** multi-source signals (social media, weather APIs, traffic data)
2. **Detects** emerging crises with confidence scoring
3. **Analyses** situations using Gemini 1.5 Pro for structured reasoning
4. **Plans** coordinated response actions
5. **Simulates** execution and visualises before/after outcomes

All orchestrated through **Google Antigravity** — no manual API chaining required.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              ☁ Google Antigravity Orchestration Layer         │
├──────────┬───────────┬────────────┬────────────┬─────────────┤
│  Signal  │   Event   │ Reasoning  │   Action   │ Simulation  │
│ Ingestion│ Detection │   Agent    │  Planning  │   Engine    │
│  Agent   │   Agent   │ (Gemini)   │   Agent    │   Agent     │
└────┬─────┴─────┬─────┴──────┬─────┴──────┬─────┴──────┬──────┘
     │           │            │            │            │
     ▼           ▼            ▼            ▼            ▼
  Raw Signals → Crisis    → Analysis  → Action    → Simulated
  (Social,     Event       (Impact,     Plan        Outcomes
   Weather,    (Type,       Urgency,    (Reroute,   (Before/
   Traffic)    Confidence)  Summary)    Dispatch)    After)
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Orchestration** | Google Antigravity, Agent Workflows, Tool-use APIs |
| **Backend / API** | Python 3.11, FastAPI, Uvicorn, Pydantic |
| **AI / LLM** | Gemini 1.5 Pro (via Antigravity), Structured Reasoning |
| **Maps** | Google Maps API (mock GeoJSON), Static Map Tiles |
| **Weather / Traffic** | Simulated OpenWeatherMap-style JSON, Mock Traffic API |
| **Mobile App** | Flutter 3.x (Dart), Provider State Management |
| **Logging / Trace** | Python structlog, Custom Agent Trace Format |
| **Dev Tools** | Git, GitHub, VS Code, Postman |

---

## 🤖 Agent Pipeline

### 1. Signal Ingestion Agent
- Ingests raw signals from social media, weather APIs, and traffic feeds
- **Bilingual support**: detects Urdu and English inputs
- Extracts locations (Pakistani sectors, named locations)
- Tags severity using keyword analysis
- Aggregates signals into `SignalBatch` objects

### 2. Event Detection Agent
- Receives `SignalBatch`, returns `CrisisEvent`
- **3 detection heuristics**: keyword clustering, cross-source corroboration, traffic anomaly detection
- Confidence scoring algorithm (multi-source bonus, severity boost)
- Severity escalation: `LOW → MEDIUM → HIGH → CRITICAL`
- Handles 4 crisis types: Flood, Heatwave, Blockage, Accident

### 3. Reasoning & Analysis Agent
- Powered by **Gemini 1.5 Pro** via Google Antigravity
- Produces structured JSON analysis: impact bullets, affected population, infrastructure risk, urgency level
- Includes fallback cache for all demo scenarios

### 4. Action Planning Agent
- Generates coordinated response actions mapped to crisis type + severity
- Examples: `reroute_traffic`, `dispatch_rescue_boats`, `send_flood_alert`, `open_relief_camp`

### 5. Simulation Engine Agent
- Executes all planned actions against a mock system state
- Tracks before/after snapshots (congestion levels, tickets, alerts)
- Generates `EmergencyTicket` and `Alert` objects
- Computes outcome metrics: congestion reduction %, response ETA, alerts dispatched

---

## 🔌 Google Antigravity Integration

> **Antigravity accounts for 25% of the evaluation score.**

| Usage | Description |
|---|---|
| **Multi-Agent Orchestration** | Defines the execution graph — which agent runs, in what order, what data it receives |
| **Tool Integration** | HTTP tools registered per agent (weather, traffic, social APIs) |
| **LLM Reasoning** | Gemini 1.5 Pro invoked via Antigravity for structured crisis analysis |
| **State Passing** | Pydantic JSON schemas passed between agents automatically |
| **Built-in Trace** | Execution traces showing every agent step, tool call, and decision |

### Agent Tool Registration

| Agent | Tools Registered | Trigger |
|---|---|---|
| `signal-ingestion` | POST `/ingest/signal`, GET `/mock/social`, `/mock/weather`, `/mock/traffic` | On new signal input |
| `event-detection` | POST `/detect/crisis` | On SignalBatch ready |
| `reasoning-analysis` | POST `/reason/analyse`, Gemini 1.5 Pro | On CrisisEvent confirmed |
| `action-planning` | POST `/plan/actions` | On CrisisAnalysis complete |
| `simulation` | POST `/simulate/execute`, GET `/maps/crisis-overlay` | On ActionPlan generated |

---

## 📱 Mobile App (Flutter)

The Flutter app provides 5 screens:

| Screen | Description |
|---|---|
| **Home Dashboard** | Before/after command centre with animated state transitions |
| **Crisis Feed** | Live list of detected crises with severity-coded cards |
| **Map View** | Google Maps with crisis overlays, blocked/alternate routes, "Run Simulation" button |
| **Alert Centre** | Dispatched alerts and emergency tickets with status tracking |
| **Agent Trace** | Vertical stepper showing the complete 5-agent reasoning chain with timing |

---

## 🌐 Web Dashboard

A real-time 2×2 panel web dashboard:
- **Live Signal Feed** — auto-polls social signals every 4 seconds
- **Agent Pipeline Status** — animated agent cards (IDLE → RUNNING → COMPLETE)
- **Crisis Detection** — confidence gauge, severity badge, explanation
- **Simulation Log** — scrolling log of tickets and alerts

Includes a **"TRIGGER PIPELINE"** button and **"Reset System"** button for demo control.

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/ingest/signal` | Submit raw signal; returns `SignalBatch` |
| `POST` | `/detect/crisis` | Detect crisis from signal batch; returns `CrisisEvent` |
| `POST` | `/reason/analyse` | AI analysis via Gemini; returns `CrisisAnalysis` |
| `POST` | `/plan/actions` | Generate action plan; returns `ActionPlan` |
| `POST` | `/simulate/execute` | Execute simulation; returns `SimulationResult` |
| `POST` | `/simulate/reset` | Reset all mock state to defaults |
| `GET` | `/simulate/state` | Current mock system state |
| `GET` | `/simulate/tickets` | List all emergency tickets |
| `GET` | `/simulate/alerts` | List all sent alerts |
| `PATCH` | `/simulate/tickets/{id}/status` | Update ticket status |
| `GET` | `/maps/crisis-overlay` | GeoJSON: crisis pin + affected area + routes |
| `GET` | `/outcome/summary` | Before/after outcome metrics |
| `GET` | `/trace/latest` | Full agent trace for most recent run |
| `GET` | `/trace/history` | Last 10 run summaries |
| `GET` | `/mock/social` | Random mock social media signal |
| `GET` | `/mock/weather` | Mock weather alert JSON |
| `GET` | `/mock/traffic` | Mock traffic congestion data |
| `GET` | `/health` | System health check |

---

## 🚀 Setup Instructions

### Backend
```bash
git clone https://github.com/shayanop/CIRO.git
cd CIRO/backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend will be available at `http://localhost:8000`. Swagger UI at `http://localhost:8000/docs`.

### Mobile App (Flutter)
```bash
cd CIRO/mobile/ciro_app
flutter pub get
flutter run
```

### Web Dashboard
Served automatically from FastAPI at `http://localhost:8000/web` after backend is running.

### Environment Variables
Create a `.env` file in `/backend`:
```env
ANTIGRAVITY_PROJECT_ID=<your-project-id>
GEMINI_API_KEY=<your-gemini-api-key>
```

---

## 🧪 Demo Scenarios

| # | Scenario | Input | Expected Output |
|---|---|---|---|
| 1 | **Urdu Flood (G-10)** | Urdu text about flooding | FLOOD detected, confidence >0.7, reroute action, map turns green |
| 2 | **English Heatwave** | English heatwave signal | HEATWAVE detected, cooling centres opened |
| 3 | **Multi-Source Flood** | Social + weather + traffic signals | CRITICAL severity, confidence >0.85, all 4 flood actions triggered |
| 4 | **Road Blockage** | Accident signal | BLOCKAGE/ACCIDENT detected, police dispatch ticket created |
| 5 | **Low Confidence** | Single vague signal | LOW severity, no critical actions triggered |

---

## 📊 Key Success Metrics

| # | Metric | Target |
|---|---|---|
| 1 | Antigravity agents configured and firing | 5 / 5 |
| 2 | Signal types handled (social, weather, traffic) | 3 / 3 |
| 3 | Crisis types detected (flood, heat, blockage, accident) | 4 / 4 |
| 4 | Confidence scoring on multi-source scenarios | ≥ 0.80 |
| 5 | Action types simulated | 4 / 4 |
| 6 | Mobile app screens complete | 5 / 5 |
| 7 | Agent trace steps per run | 5 / 5 |
| 8 | API endpoint response time | < 500ms |
| 9 | Demo video duration | 3–5 min |
| 10 | E2E test scenarios passing | 5 / 5 |

---

## ⚠️ Assumptions

- All weather, traffic, and social media data is **simulated/mock** for the hackathon scope.
- Google Maps API calls use **pre-saved GeoJSON** to avoid quota issues.
- Gemini responses are **cached** for all 5 demo scenarios as fallback.
- The mobile app targets **Android** as the primary demo platform.
- All agents communicate via **REST API** endpoints orchestrated through Antigravity.

---

## 👥 Team

| Name | Role |
|---|---|
| **Anas** | Lead Engineer – Antigravity & Signal Ingestion |
| **Hasnain** | AI Engineer – Event Detection & Maps |
| **Arshman** | Backend Dev – Reasoning & Simulation |
| **Saad** | Mobile Dev – Flutter App & UX |
| **Shayan** | Systems Dev – Logging, Docs & Demo |

---

## 📄 Documentation

- [`Plans/CIRO_Implementation_Plan_5_Days.md`](Plans/CIRO_Implementation_Plan_5_Days.md) – 5-Day Sprint Plan
- `docs/ARCHITECTURE.md` – System Architecture
- `docs/AGENT_DESIGN.md` – Agent Design Specifications
- `docs/API_REFERENCE.md` – Full API Documentation
- `docs/ASSUMPTIONS.md` – Project Assumptions & Boundaries
- `docs/DEMO_SCRIPT.md` – Demo Video Script
- `docs/sample_trace.json` – Sample Agent Trace Output

---

<p align="center">
  <b>CIRO – Crisis Intelligence & Response Orchestrator</b><br>
  Challenge 3 · Google Antigravity Hackathon
</p>
