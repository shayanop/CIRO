# CIRO - Crisis Intelligence & Response Orchestrator
## 5-Day Implementation Plan

### 1. Project Overview & Strategy
**What We Are Building**
CIRO is an Agentic AI System that ingests multi-source signals (social media, weather APIs, traffic maps), detects emerging urban crises, generates coordinated response actions, simulates their execution, and visualises outcomes – all orchestrated through Google Antigravity using Gemini for AI reasoning.

**System Architecture**
Signal Ingestion -> Event Detection -> Reasoning Agent -> Action Planning -> Simulation Engine
*(All orchestrated by the Google Antigravity Layer)*

### 2. Team Roles & Responsibilities
- **Anas (Lead Engineer)**: Antigravity Setup, Signal Ingestion Agent, Full System Integration
- **Hasnain (AI Engineer)**: Event Detection Agent, FastAPI Scaffold, Maps Integration, Web Dashboard
- **Arshman (Backend Dev)**: Reasoning Agent, Mock Data Factory, Alert & Tickets, Docs
- **Saad (Mobile Dev)**: Flutter App Initialization, Action Planner, Mobile Screens, E2E Testing
- **Shayan (Systems Dev)**: Architecture Docs, Antigravity Pipeline Wiring, Trace Logging, Demo Recording

### 3. Sprint Overview
- **Day 1**: Foundation & Environment Setup
- **Day 2**: Core Agent Implementation
- **Day 3**: Simulation Layer & Mobile Core
- **Day 4**: Polish, Visualisation & Web Dashboard
- **Day 5**: Integration, Recording, Final Docs & Submission

---

### 4. Day-by-Day Implementation Plan

#### Day 1: Foundation & Environment Setup
**Goal**: All systems are live, repos initialised, and every team member has a running local environment.
- **All**: Stand-up call, create GitHub org, clone monorepo (`/backend`, `/mobile`, `/web`, `/docs`), install base tools.
- **Anas**: Set up Google Antigravity project, create 5 core agents, register HTTP tools, and export YAML config.
- **Hasnain**: Set up FastAPI Backend Scaffold, define folder structure, implement mock routers, and ensure Swagger UI is live.
- **Arshman**: Build Mock Data Factory, create simulated social signals/weather/traffic data, and define Pydantic models.
- **Saad**: Initialize Flutter App, set up folder structure, install dependencies, and create basic 5 screens.
- **Shayan**: Create Architecture documentation, agent design specs, logger utility, and project assumptions.

#### Day 2: Core Agent Implementation
**Goal**: All five AI agents are functional. Each performs its designated reasoning task independently.
- **Anas**: Implement Signal Ingestion Agent (language detection, location extraction, severity tagging).
- **Hasnain**: Implement Event Detection Agent (confidence scoring, severity escalation, cross-source heuristics).
- **Arshman**: Implement Reasoning & Situation Analysis Agent (integrate Gemini via Antigravity, add fallback cache).
- **Saad**: Implement Action Planning Agent (action generation rules) and Crisis Feed Screen in Flutter.
- **Shayan**: Complete Antigravity Pipeline wiring, map data schemas between agents, and set up the trace logging system.

#### Day 3: Simulation Layer & Mobile Core
**Goal**: The simulation engine executes all action types and records state changes. Mobile app shows map with crisis overlays.
- **Anas**: Build Action Simulation Engine (mock system state, implement action handlers for rerouting, dispatching, etc.).
- **Hasnain**: Integrate Google Maps API mock, pre-save GeoJSON overlays for crises, and implement static map endpoints.
- **Arshman**: Create Alert & Emergency Ticket System models and status update endpoints.
- **Saad**: Build Mobile Map & Alerts Screens, integrate GeoJSON rendering, and "Run Simulation" functionality.
- **Shayan**: Implement full Agent Trace Logging REST endpoints (store steps, capture durations).

#### Day 4: Polish, Visualisation & Web Dashboard
**Goal**: Full end-to-end user experience is complete. App is demo-ready.
- **Anas**: Implement Outcome Visualisation endpoint (compute congestion reduction, ETA, alerts dispatched) and Flutter Command Dashboard.
- **Hasnain**: Build Web Dashboard (Live signal feed, animated agent pipeline, crisis detection panel, simulation log).
- **Arshman**: Polish Mobile App UX (consistent design, empty states, error handling, bilingual input screen).
- **Saad**: Build Agent Trace Screen in Flutter and run/document 5 End-to-End Test Scenarios.
- **Shayan**: Finalize demo script, configure OBS recording setup, and record a test run.

#### Day 5: Integration, Recording, Final Docs & Submission
**Goal**: Record final demo video, complete all docs, verify system stability, and submit the project.
- **Anas**: Merge all branches, perform full system integration testing, fix breakages, and tag the final release.
- **Hasnain**: Fix high-priority bugs, implement response caching, and ensure all endpoints respond in <500ms.
- **Arshman**: Finalize README.md, write full API reference documentation, and ensure all links work.
- **Saad**: Run dry run demo on physical device, build release APK, and capture final screenshots.
- **Shayan**: Record the final 3-5 minute demo video, edit it, upload it, and add the link to the README.
- **All**: Perform individual checklists, run the full demo live together, and proceed with the final submission.

---

### 5. Google Antigravity Integration (Key Highlights)
- **Multi-Agent Orchestration**: Defines execution graph and triggers.
- **Tool Integration**: HTTP tools registered for weather/traffic APIs.
- **LLM Reasoning**: Gemini 1.5 Pro used for structured analysis.
- **State Passing**: Pydantic JSON schemas passed autonomously.

### 6. Risk Management & Fallbacks
- Prepare fallback mock demo modes in FastAPI if Antigravity portal is down.
- Pre-save all GeoJSON and Gemini responses to avoid API quotas and rate limits.
