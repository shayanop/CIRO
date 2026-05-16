# CIRO – Final Sprint Plan (2 Days, 5 Independent Tracks)

> Goal: take the repo from its current state to a fully demo-ready, judge-ready submission. No deliverable is dropped — backend intelligence, web dashboard, Flutter mobile app, Antigravity orchestration, docs, and demo video all ship.

## How to Use This Plan

- **Task 1 is the foundation track.** It contains shared pre-requisites that everything else depends on. Anyone starting on Tasks 2–5 should pull `main` after Task 1 lands, or build against the contracts defined here without waiting (every artifact Task 1 ships is documented below).
- **Tasks 2–5 are fully independent of each other.** A single person can complete any one of them end-to-end without coordinating with the other tracks. Pick a track, finish it, ship it.
- Each track lists: scope, files touched, acceptance criteria, and a recommended order of sub-steps.

---

## Track 1 — Foundation & Shared Pre-requisites

**Why first:** ships the contracts the other tracks consume (a single `/pipeline/run` endpoint, a complete `.env.example`, GeoJSON overlays for every demo location, an extended location/keyword list, an auto-ingest endpoint, pinned requirements). Once Task 1 is merged, Tracks 2–5 have zero blocking dependencies on each other.

### 1.1 — Single-call pipeline endpoint
- **Files:** new `backend/routers/pipeline.py`, `backend/main.py`
- **Do:** Add `POST /pipeline/run` that takes a `RawSignalInput` and internally invokes ingest → detect → reason → plan → simulate. Returns one `PipelineResult` object with `run_id`, `batch`, `event`, `analysis`, `plan`, `simulation`. Auto-completes the trace run at the end.
- **Done when:** A single POST returns the full 5-agent output in under 2 seconds; `/trace/latest` shows 5 steps.

### 1.2 — Environment template
- **Files:** new `.env.example`
- **Do:** Document every env var the project reads: `GROQ_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_MAPS_API_KEY`, `ANTIGRAVITY_PROJECT_ID`, `BACKEND_URL`. Add inline comments on which feature each unlocks.
- **Done when:** `cp .env.example .env` is the only setup step needed for a fresh clone.

### 1.3 — Complete GeoJSON overlay library
- **Files:** new `backend/data/g10_flood_overlay.json`, `george_town_overlay.json`, `f6_flood_overlay.json`, `jacobabad_heatwave_overlay.json`, `shahrah_faisal_blockage_overlay.json`, `karachi_cyclone_overlay.json`, `murree_landslide_overlay.json`
- **Do:** Real GeoJSON-style overlays matching the schema in `services/maps_service.py`: `crisis_pin {lat,lng}`, `affected_polygon [{lat,lng}...]`, `primary_route {name, polyline, status, color}`, `alternate_route {name, polyline, status, color}`. Use realistic coordinates per location.
- **Done when:** `GET /maps/crisis-overlay?location=<each>` returns file-backed data (not inline fallback) for all 7 locations.

### 1.4 — Extend location & keyword coverage
- **Files:** `backend/routers/ingest.py`
- **Do:** Expand `NAMED_LOCATIONS` to cover every location in `data/social_signals.json` (G-6 through G-13, F-6 through F-11, I-8/9/10/11, E-7/11, Murree, Multan, Bahawalpur, Sukkur, Hyderabad, Peshawar, Quetta, Faisalabad, Sialkot, Gujranwala, Mardan, Nowshera, Mall Road, Liberty Roundabout, Hunza, Chitral, DHA Phase 5, Bahria Town, Tariq Road, Lyari Expressway, Super Highway, Karachi Airport, Diplomatic Enclave, Saddar, etc.). Add Urdu keywords for the new crisis types: `dhamaka`, `aag`, `zalzala`, `landslide`, `tornado`, `chhat gir`, `cylinder blast`, `firing`, `tasadum`. Add new crisis-type buckets: `FIRE`, `EARTHQUAKE`, `STORM` in `CrisisType` enum, plumbed through `detect.py` and `plan.py`.
- **Done when:** A random 20-signal sample from the JSON file all yield non-null `location` after `process_signal`; all new crisis types pass through detect → plan.

### 1.5 — Auto-ingest endpoint
- **Files:** `backend/routers/ingest.py` (extend)
- **Do:** Add `POST /ingest/auto` that reads `data/weather_mock.json` alerts and `data/traffic_mock.json` blocked routes, converts each into `RawSignalInput`, runs them through the pipeline, returns the resulting `SignalBatch`. Lets the demo trigger multi-source corroboration without hand-crafted POSTs.
- **Done when:** One call produces a batch with ≥3 signals from ≥2 sources, primary_location auto-resolved.

### 1.6 — Hygiene
- **Files:** delete `backend/b:tmp_batch.json`, extend `.gitignore` for `__pycache__/`, `.pytest_cache/`, `.env`, `*.pyc`, `.venv/`. Pin versions in `backend/requirements.txt` and add `groq`, `google-adk`, `python-dotenv`, `pytest-asyncio`, `httpx`.
- **Done when:** `git status` is clean; `pytest` runs green.

### 1.7 — Pipeline contract documentation
- **Files:** new `docs/PIPELINE_CONTRACT.md`
- **Do:** Document the exact JSON shape returned by `/pipeline/run` so Tracks 3 and 4 (web & mobile) can build against it without reading backend source.
- **Done when:** Sample response is committed and matches what the endpoint actually emits.

**Track 1 acceptance:** every other track has the endpoints, env keys, overlay files, location list, and contract docs it needs.

---

## Track 2 — Backend Intelligence Layer

**Independent of:** Tracks 3, 4, 5. Builds on Track 1 contracts.

### 2.1 — Groq LLM integration in Reasoning Agent
- **Files:** `backend/routers/reason.py`, `backend/requirements.txt`
- **Do:** Add `groq` package. Call `llama-3.3-70b-versatile` with `response_format={"type":"json_object"}`. Build prompt from `CrisisEvent` (type, location, severity, signals + their content). Parse JSON into `CrisisAnalysis`. On any exception (no API key, timeout, rate limit, JSON parse failure) fall back to existing `_get_cached_analysis`. Add 5s timeout, retry once. Keep the entire fallback cache intact so demo never breaks.
- **Done when:** `POST /reason/analyse` returns model-generated impact bullets when `GROQ_API_KEY` is set; identical-shape cache response otherwise. Bilingual (Urdu input → English structured output) works.

### 2.2 — Multi-source corroboration in Detection Agent
- **Files:** `backend/routers/detect.py`
- **Do:** Add three confidence bonuses:
  - **Engagement bonus:** +0.05 if any signal has engagement >500, +0.10 if >2000, +0.15 if >5000.
  - **Weather corroboration:** load `data/weather_mock.json`, if any signal's location matches an alert's region AND crisis_type aligns with alert event, +0.15.
  - **Traffic corroboration:** load `data/traffic_mock.json`, if any signal's location matches a route with status `blocked`, +0.15.
- **Done when:** A flood signal from G-10 combined with the rain alert and a blocked route hits confidence ≥ 0.85 → CRITICAL severity.

### 2.3 — Full backend test suite
- **Files:** new `backend/tests/test_detect.py`, `test_plan.py`, `test_simulate.py`, `test_reason.py`, `test_outcome.py`, `test_trace.py`, `test_pipeline.py`
- **Do:**
  - Detect: confidence math, crisis-type classification, severity thresholds, corroboration bonuses (≥15 tests).
  - Plan: every `(crisis_type, severity)` key in `ACTION_RULES` (≥12 tests).
  - Simulate: each action handler mutates state correctly, `/reset` clears state, before/after snapshots (≥12 tests).
  - Reason: cache hit on every key, fallback when LLM disabled (≥8 tests).
  - Outcome: congestion math, ETA aggregation (≥6 tests).
  - Trace: log_step, get_latest, get_history, reset (≥6 tests).
  - Pipeline: end-to-end happy path + 5 demo scenarios (≥6 tests).
- **Done when:** `pytest` returns ≥75 passing tests, no skips, coverage ≥80% across `routers/`.

### 2.4 — Response caching & performance
- **Files:** `backend/services/cache.py` (new), wire into `reason.py`
- **Do:** Add an in-memory LRU cache (functools or cachetools) keyed by `(event_id, crisis_type, severity)` for LLM analyses. TTL 10 minutes. Cuts demo latency to <100ms on repeats.
- **Done when:** Hitting `/reason/analyse` twice with the same event returns the second call in under 50ms.

### 2.5 — Severity escalation & deduplication
- **Files:** `backend/routers/detect.py` extended
- **Do:** If the same location has produced ≥2 events of the same crisis type in the last 5 minutes (`trace_store` history), auto-bump severity by one level and add an `escalated: true` flag to the explanation. Prevents duplicate alerts in the demo.
- **Done when:** Replaying the Urdu flood scenario twice in quick succession produces a CRITICAL on the second run.

**Track 2 acceptance:** LLM-powered analysis, smarter detection, comprehensive tests, sub-100ms cached responses.

---

## Track 3 — Web Dashboard

**Independent of:** Tracks 2, 4, 5. Builds on Track 1's `/pipeline/run` contract.

### 3.1 — Live Signal Feed panel
- **Files:** `web/app.js`, `web/style.css`
- **Do:** Poll `/mock/social` every 4 seconds. Animate new signals sliding in from the top. Show language flag (🇬🇧 EN / 🇵🇰 UR), source icon (Twitter / Facebook), engagement count, location chip, severity dot. Cap at 15 visible cards. Pause polling when "Reset System" is clicked.
- **Done when:** Loading the dashboard auto-streams signals; reset clears feed; pausing tab pauses polling.

### 3.2 — Animated Agent Pipeline panel
- **Files:** `web/app.js`, `web/style.css`
- **Do:** When "Trigger Pipeline" is clicked, hit `POST /pipeline/run`. Visually animate each of 5 agent cards IDLE → RUNNING (pulse) → COMPLETE (green checkmark) in sequence with realistic per-step timing (poll `/trace/latest` to drive transitions, or sequence on timeouts derived from the response). Show duration_ms on each card after completion.
- **Done when:** Every trigger animates all 5 agents with timings; failures show RED ERROR state.

### 3.3 — Crisis Detection panel
- **Files:** `web/app.js`, `web/style.css`
- **Do:** Render confidence as a circular gauge (CSS conic-gradient or SVG). Severity badge (color-coded: green/yellow/orange/red). Crisis type icon (water drop / sun / cone / car / fire). One-line explanation. Bilingual-aware (show "URDU" tag when input was Urdu).
- **Done when:** After every trigger, the panel reflects the latest `CrisisEvent` payload from `/pipeline/run`.

### 3.4 — Simulation Log panel
- **Files:** `web/app.js`, `web/style.css`
- **Do:** Scrolling log of tickets (📋 `ticket_id` · unit · ETA) and alerts (📢 channel · recipients_count · target_area), pulled from the `simulation.tickets_created` and `alerts_sent` arrays of `/pipeline/run`. Most recent on top, fade-in animation, auto-scrolls.
- **Done when:** Each pipeline run appends new entries; reset clears the log.

### 3.5 — Live Map panel (4th quadrant or full-width below)
- **Files:** `web/index.html`, `web/app.js`, `web/style.css`
- **Do:** Use Leaflet + OpenStreetMap tiles (free, no key). After `/pipeline/run`, fetch `/maps/crisis-overlay?location=<event.location>` and render: crisis pin, affected polygon (red translucent), blocked primary route (red line), recommended alternate route (green dashed). Auto-fit bounds to the affected area.
- **Done when:** Every demo scenario shows a correct map overlay; map updates on each pipeline run.

### 3.6 — Agent Reasoning Trace panel
- **Files:** `web/index.html`, `web/app.js`, `web/style.css`
- **Do:** Collapsible section below the 2×2 grid. After each pipeline run, fetch `/trace/latest` and render a vertical stepper of the 5 agents. Each step is expandable to show input JSON, output JSON, duration_ms. This panel showcases Antigravity's value to judges.
- **Done when:** Every run renders a 5-step trace; each step toggles open/closed with JSON syntax highlighting (use a tiny lib like Prism or hand-roll).

### 3.7 — Outcome Visualization
- **Files:** `web/app.js`, `web/style.css`
- **Do:** After each pipeline run, fetch `/outcome/summary` and render before/after metric cards: `congestion_reduction_pct`, `vehicles_rerouted`, `min_eta_minutes`, `alerts_dispatched`, `tickets_created`. Animate number counters from 0 → final value.
- **Done when:** Outcome panel updates with real numbers after every trigger.

**Track 3 acceptance:** Complete real-time web dashboard with 6 working panels + trace view, no mocked data.

---

## Track 4 — Flutter Mobile App

**Independent of:** Tracks 2, 3, 5. Builds on Track 1's contracts.

### 4.1 — Project scaffold
- **Files:** new `frontend/ciro_app/*` (`flutter create`)
- **Do:** Initialize Flutter project under `frontend/ciro_app/`. Dependencies: `http`, `provider`, `flutter_map`, `latlong2`, `intl`. Set up theme (dark, gradient accents matching CIRO branding). Create `lib/services/api_client.dart` wrapping every backend endpoint. Create `lib/models/` mirroring backend Pydantic models. Bottom nav with 5 tabs.
- **Done when:** `flutter run` opens app with 5-tab navigation; API client compiles.

### 4.2 — Home Dashboard screen
- **Files:** `lib/screens/home_screen.dart`
- **Do:** "Command Centre" view. Top: live status card (system OK, last run timestamp). Two large "BEFORE" and "AFTER" comparison cards driven by `/outcome/summary` with animated transitions on new data. Quick stats: total tickets, alerts, congestion delta. Floating Action Button: "TRIGGER PIPELINE" calling `/pipeline/run` with a default scenario.
- **Done when:** Screen reflects live backend state, FAB triggers a full run.

### 4.3 — Crisis Feed screen
- **Files:** `lib/screens/crisis_feed_screen.dart`
- **Do:** List of detected crisis events (poll `/trace/history` every 5s). Severity-coded cards (LOW=green, MEDIUM=yellow, HIGH=orange, CRITICAL=red). Each card: crisis type icon, location, confidence %, summary from analysis, "view details" button → bottom sheet showing the full `CrisisAnalysis`.
- **Done when:** New crises appear automatically; tapping a card opens details.

### 4.4 — Map View screen
- **Files:** `lib/screens/map_screen.dart`
- **Do:** `flutter_map` with OSM tiles. Marker for current crisis pin. Polygon for affected area (red). Polyline for blocked route (red) and alternate (green dashed). Pulls from `/maps/crisis-overlay`. "Run Simulation" button executes `/simulate/execute` against the latest plan, then re-fetches the overlay so routes update.
- **Done when:** Map renders for every demo location; Run Simulation visually updates routes.

### 4.5 — Alert Centre screen
- **Files:** `lib/screens/alerts_screen.dart`
- **Do:** Two tabs: Alerts (`/simulate/alerts`) and Tickets (`/simulate/tickets`). Alerts show channel icon, message, target area, recipient count, sent time. Tickets show unit dispatched, location, ETA, status. Tickets have a status chip the user can tap to PATCH `/simulate/tickets/{id}/status` from `dispatched` → `resolved`.
- **Done when:** Both lists render; status update reflects on backend.

### 4.6 — Agent Trace screen
- **Files:** `lib/screens/trace_screen.dart`
- **Do:** Vertical stepper with 5 agent steps from `/trace/latest`. Each step: agent name, step name, duration_ms, expandable input/output JSON. Pull-to-refresh re-fetches. Color-coded by agent (signal=blue, detect=purple, reason=pink, plan=orange, simulate=green).
- **Done when:** Trace fully reflects the latest run with expandable JSON.

### 4.7 — Bilingual input bottom sheet
- **Files:** `lib/widgets/bilingual_input.dart`
- **Do:** Reusable bottom sheet with a text field, source dropdown (social/weather/traffic), language toggle (EN/UR), and "Submit Signal" button. Posts to `/ingest/signal` then auto-triggers `/pipeline/run`. Accessible from Home FAB and Crisis Feed.
- **Done when:** User can type an Urdu or English signal and watch the whole pipeline react.

### 4.8 — Build & package
- **Files:** `frontend/ciro_app/android/app/build.gradle`
- **Do:** Build release APK (`flutter build apk --release`). Drop the APK in `docs/releases/CIRO-v1.0.apk`. Take 5 screenshots (one per screen) into `docs/screenshots/`.
- **Done when:** APK installs cleanly on Android; screenshots committed.

**Track 4 acceptance:** All 5 screens working against the live backend, release APK shipped, screenshots in docs.

---

## Track 5 — Antigravity Orchestration, Docs & Demo

**Independent of:** Tracks 2, 3, 4. Builds on Track 1's contracts.

### 5.1 — Antigravity / Google ADK pipeline end-to-end
- **Files:** `backend/agents/ciro_pipeline.py`, new `docs/ANTIGRAVITY.md`
- **Do:** Install `google-adk`. Verify `adk web agents` opens the UI and all 5 agents register. Fix any tool-signature bugs (verify each tool actually hits the FastAPI endpoint via httpx). Capture screenshots of the agent graph executing the Urdu flood scenario. Document setup steps in `ANTIGRAVITY.md`: required env vars, how to launch, how to trigger a scenario, what to expect.
- **Done when:** `adk web` runs the full 5-agent pipeline against the FastAPI backend and produces a valid simulation result; documentation includes 3+ screenshots.

### 5.2 — Five end-to-end scenario runner
- **Files:** new `backend/scripts/run_scenarios.py`, new `docs/DEMO_SCENARIOS.md`
- **Do:** Standalone Python script that hits the running backend with the 5 scenarios from the README:
  1. Urdu flood G-10
  2. English heatwave (Jacobabad / Karachi)
  3. Multi-source flood (social + weather + traffic)
  4. Road blockage (Shahrah-e-Faisal)
  5. Low confidence (single vague signal)
  Prints PASS/FAIL for each with expected vs actual confidence, severity, crisis type, action count. Document each scenario in markdown (input, expected output, what the judge should watch for).
- **Done when:** `python scripts/run_scenarios.py` prints 5/5 PASS against a running backend.

### 5.3 — Full API reference
- **Files:** new `docs/API_REFERENCE.md`
- **Do:** For every endpoint in `main.py` (~24 routes), document: method, path, request schema (JSON example), response schema (JSON example), curl example. Group by router (Ingestion, Detection, Reasoning, Planning, Simulation, Maps, Outcome, Trace, Mock, System).
- **Done when:** Every endpoint registered in `main.py` has a complete entry; markdown renders cleanly on GitHub.

### 5.4 — README polish + Quick Demo section
- **Files:** `README.md`
- **Do:** Reflect reality: current endpoint list, current mobile setup, both Groq and Gemini env vars, mention web dashboard URL. Add a "Quick Demo" section with 3 curl commands that demonstrate the pipeline end-to-end. Add badges for test count and Antigravity. Update the team table layout if needed.
- **Done when:** A fresh clone follows README setup and reaches a working demo in under 5 minutes.

### 5.5 — Architecture diagrams
- **Files:** new `docs/diagrams/system_architecture.png`, `agent_pipeline.png`, `data_flow.png`
- **Do:** Three diagrams (Mermaid → PNG, or draw.io export). System architecture showing all components (backend, web, mobile, Antigravity, Gemini, mock data). Agent pipeline showing data flow Signal → Batch → Event → Analysis → Plan → Simulation. Data flow showing mock data files feeding the pipeline.
- **Done when:** Three diagrams render cleanly in `docs/`, linked from README.

### 5.6 — Demo script + sample trace
- **Files:** new `docs/DEMO_SCRIPT.md`, new `docs/sample_trace.json`
- **Do:** Shot-by-shot 3–5 minute script:
  - 0:00 – Problem statement (Pakistan urban crises, fragmented response)
  - 0:30 – Architecture diagram walkthrough
  - 1:00 – Open web dashboard, click TRIGGER PIPELINE with Urdu flood signal
  - 1:30 – Watch all 5 agent cards animate IDLE → RUNNING → COMPLETE
  - 2:00 – Map updates with crisis overlay + alternate route
  - 2:30 – Open Reasoning Trace, show JSON input/output of each agent
  - 3:00 – Run multi-source CRITICAL scenario, show severity escalation
  - 3:30 – Open Flutter app (release APK), walk through 5 screens
  - 4:00 – Switch to Antigravity UI, show the same pipeline orchestrated by ADK
  - 4:30 – Close with metrics: agents firing, scenarios passing, response time
  Save a real captured trace JSON from a live run into `docs/sample_trace.json`.
- **Done when:** Script is shot-by-shot timed; `sample_trace.json` is real and committed.

### 5.7 — Demo video recording
- **Files:** new `docs/demo_video.md` (link only — actual video on YouTube/Drive)
- **Do:** Record the 3–5 minute video using OBS following the script. Edit in DaVinci Resolve or Shotcut. Upload as unlisted YouTube video. Add link to README header.
- **Done when:** Video is uploaded, link in README, runs under 5 minutes, audio clear.

### 5.8 — Assumptions & limitations doc update
- **Files:** `docs/Assumptions.md`
- **Do:** Update with current scope: mock data sources, cached Gemini fallback, free-tier LLM (Groq), no real-time GPS, Android-only mobile, etc. List explicitly what would change for production.
- **Done when:** Doc reflects shipped state, not aspirational state.

**Track 5 acceptance:** Antigravity demonstrably orchestrating the pipeline, complete docs, demo video uploaded, README polished.

---

## Risk Hedges (Built Into Every Track)

- **Every LLM call has a fallback cache** (Track 2.1 preserves the existing `FALLBACK_CACHE`)
- **Every map call has an inline overlay fallback** (Track 1.3 adds files; `services/maps_service.py` already has inline `_INLINE_OVERLAYS`)
- **Tests in Track 2.3 catch regressions** from parallel work
- **Scenario runner (Track 5.2) is a pre-flight check** before the live demo
- **Sample trace + recorded video (Tracks 5.6, 5.7)** mean even if the live demo fails, the submission has a working artifact

---

## What Each Track Outputs (Submission Checklist)

| Track | Deliverable |
|---|---|
| 1 | `/pipeline/run`, `.env.example`, 7 GeoJSON overlay files, extended location/keyword coverage, `/ingest/auto`, pinned requirements, contract doc |
| 2 | Real Groq LLM in reasoning agent, smarter detection with corroboration, 75+ tests, response cache, severity escalation |
| 3 | 6-panel real-time web dashboard with live signals, animated pipeline, gauge, sim log, Leaflet map, trace stepper, outcome cards |
| 4 | Flutter app with 5 screens, bilingual input, release APK, screenshots |
| 5 | Working Antigravity ADK pipeline, scenario runner, full API reference, polished README, 3 architecture diagrams, demo script, sample trace, recorded video |

All five tracks together = a complete, polished, judge-ready CIRO submission.
