# 🧠 Hasnain – AI Engineer: Event Detection & Maps
## Individual 5-Day Plan

> **Role**: Build the Event Detection Agent, own the FastAPI backend scaffold, integrate Google Maps API, and produce the web dashboard.

---

## Day 1 – FastAPI Backend Scaffold

### Pre-Meeting (All Members)
- [ ] Join stand-up call on Google Meet
- [ ] Clone the monorepo and create feature branch: `git checkout -b feat/hasnain-day1`

### Backend Setup
- [ ] `cd backend && python -m venv venv && venv\Scripts\activate`
- [ ] `pip install fastapi uvicorn pydantic python-dotenv httpx structlog`
- [ ] `pip freeze > requirements.txt`
- [ ] Create the exact folder structure inside `/backend`:
  ```
  backend/
    main.py                # FastAPI entrypoint
    .env                   # API keys (gitignored)
    requirements.txt
    routers/
      ingest.py            # POST /ingest/signal
      detect.py            # POST /detect/crisis
      reason.py            # POST /reason/analyse
      plan.py              # POST /plan/actions
      simulate.py          # POST /simulate/execute
      maps.py              # GET /maps/crisis-overlay
      outcome.py           # GET /outcome/summary
      trace.py             # GET /trace/latest
      mock.py              # GET /mock/weather | traffic | social
    models/
      signal.py            # Signal, SignalBatch, CrisisEvent
      simulation.py        # EmergencyTicket, Alert, SimulationResult
      response.py          # All response schemas
    services/
      antigravity.py       # Antigravity API wrapper
      maps_service.py      # Google Maps API (mock)
      alert_service.py     # Alert simulation
      trace_store.py       # In-memory trace accumulator
    data/
      social_signals.json
      weather_mock.json
      traffic_mock.json
    tests/
      test_ingest.py
      test_detect.py
    utils/
      logger.py            # structlog setup
  ```
- [ ] Write `main.py`: import all routers, add CORS middleware (`allow_origins=["*"]`), mount routers with prefixes, run Uvicorn on port 8000
- [ ] Write stub handlers in each router returning `{"status": "stub", "module": "<name>"}`
- [ ] Run `uvicorn main:app --reload` – open `http://localhost:8000/docs` and verify all routes appear in Swagger UI
- [ ] Commit: `"feat: fastapi scaffold, all routers, swagger confirmed"`

### ✅ End of Day Deliverable
Running FastAPI server, Swagger UI accessible, all 16 routes responding 200.

---

## Day 2 – Event Detection Agent

- [ ] Open `/backend/routers/detect.py`
- [ ] Implement **POST /detect/crisis** – accepts `SignalBatch`, returns `CrisisEvent`

### 3 Detection Heuristics
- [ ] **Heuristic 1 – Keyword Cluster**: If ≥2 signals share flood keywords AND same location → `crisis_type = FLOOD`
- [ ] **Heuristic 2 – Cross-Source Corroboration**: If social signal AND weather API both have rain/flood → `confidence += 0.35`
- [ ] **Heuristic 3 – Traffic Anomaly**: If any route has `congestion_level > 70` → `crisis_type = BLOCKAGE`

### Confidence Scoring Algorithm
- [ ] Implement the scoring function:
  ```python
  def compute_confidence(signals: list, crisis_type: str) -> float:
      score = 0.0
      # Base score from signal count
      if len(signals) >= 3: score += 0.30
      elif len(signals) == 2: score += 0.15
      else: score += 0.05
      
      # Multi-source bonus
      sources = {s.source for s in signals}
      if len(sources) >= 3: score += 0.40
      elif len(sources) == 2: score += 0.25
      
      # Severity boost
      if any(s.severity_hint == "high" for s in signals):
          score += 0.30
      elif any(s.severity_hint == "medium" for s in signals):
          score += 0.15
      
      return min(round(score, 2), 1.0)
  ```

### Severity Escalation
- [ ] confidence > 0.8 → CRITICAL
- [ ] 0.6–0.8 → HIGH
- [ ] 0.4–0.6 → MEDIUM
- [ ] < 0.4 → LOW

### Testing & Registration
- [ ] Register endpoint in Antigravity on `event-detection-agent`
- [ ] Write tests: single-source low confidence vs. multi-source high confidence
- [ ] Run with pytest
- [ ] Commit: `"feat: event detection agent with confidence scoring and severity escalation"`

### ✅ End of Day Deliverable
Agent correctly classifies flood, heatwave, blockage with confidence scores.

---

## Day 3 – Google Maps Integration

- [ ] Create `/backend/services/maps_service.py`

### Pre-saved GeoJSON Data
- [ ] Create `data/g10_flood_overlay.json`: crisis pin at G-10 centroid, affected area polygon (red), alternate route polyline via Margalla Road (green)
- [ ] Create `data/george_town_overlay.json`: crisis pin at George Town, reroute via M.A.Jinnah Road

### Maps Endpoints
- [ ] Implement **GET /maps/crisis-overlay** endpoint:
  - Accept query param `?location=G-10`
  - Load matching pre-saved GeoJSON overlay file
  - Return: `{crisis_pin: {lat, lng}, affected_polygon: [...], primary_route: {polyline, status: "BLOCKED"}, alternate_route: {polyline, status: "ACTIVE"}}`
- [ ] Implement **GET /maps/static-map**: call Google Static Maps API with crisis marker and return image URL (or use pre-downloaded PNG)
- [ ] Test `/maps/crisis-overlay?location=G-10` via Postman – verify GeoJSON structure is valid

### Route Library
- [ ] Create `/data/route_library.json`: 5 pre-defined alternate route polylines for common Islamabad/Karachi crisis locations
- [ ] Commit: `"feat: maps service, pre-saved overlays, crisis overlay endpoint"`

### ✅ End of Day Deliverable
Maps endpoint returns valid GeoJSON with crisis pin and alternate routes.

---

## Day 4 – Web Dashboard

- [ ] Create `/web/index.html`, `/web/style.css`, `/web/app.js`

### HTML Layout – 4 Panels in 2×2 Grid
- [ ] **Panel 1 (top-left) – Live Signal Feed**: auto-polls `GET /mock/social` every 4 seconds. Shows last 5 signals as scrolling cards
- [ ] **Panel 2 (top-right) – Agent Pipeline Status**: 5 agent step cards. Each starts grey (IDLE), turns yellow (RUNNING), turns green (COMPLETE). Polls `GET /trace/latest` every second during run
- [ ] **Panel 3 (bottom-left) – Crisis Detection**: shows crisis type, large confidence gauge (CSS animated arc), severity badge, explanation text
- [ ] **Panel 4 (bottom-right) – Simulation Log**: scrolling log of tickets and alerts as they are created. Colour coded by type

### Controls
- [ ] Large red **"TRIGGER PIPELINE"** button at the top. On click: POST to `/ingest/signal` with a random sample signal, then start polling `/trace/latest` every 500ms to animate agents
- [ ] CIRO header with logo text and current timestamp auto-updating
- [ ] **"Reset System"** button calling `POST /simulate/reset`

### Serve from FastAPI
- [ ] Add `app.mount("/web", StaticFiles(directory="web"))` to `main.py`
- [ ] Test in Chrome – confirm the whole demo scenario auto-animates within 10 seconds
- [ ] Commit: `"feat: web dashboard with live pipeline, agent animations, simulation log"`

### ✅ End of Day Deliverable
Web dashboard is demo-ready with live animation of the full pipeline.

---

## Day 5 – Bug Fixes, Performance & Submission

### Bug Fixes & Performance (Morning)
- [ ] Review all open GitHub issues. Fix priority bugs (P0 = crash, P1 = wrong data, P2 = cosmetic)
- [ ] Add response caching: `functools.lru_cache` on `/mock/weather` and `/mock/traffic`
- [ ] Add 5-second timeout to all Antigravity API calls with cached fallback response
- [ ] Add health endpoint: `GET /health` → `{"status": "ok", "agents": 5, "version": "1.0"}`
- [ ] Test web dashboard in Chrome, Firefox – fix any rendering issues
- [ ] Verify all API endpoints respond in under 500ms using Postman's collection runner
- [ ] Commit: `"fix: all P0/P1 bugs resolved, caching added, health endpoint"`

### Demo Recording (Afternoon – All Members)
- [ ] Join Google Meet. Role: **Manage web dashboard** during recording
- [ ] Participate in 3 recording takes
- [ ] Assist with final submission

### ✅ End of Day Deliverable
Zero critical bugs. All endpoints under 500ms response time. Demo recorded and submitted.

---

## Dependencies & Coordination Points
| With | What | When |
|---|---|---|
| **Anas** | Antigravity project ID and API keys for `.env` | Day 1 |
| **Arshman** | Mock data JSON files needed for stub endpoints | Day 1 |
| **Saad** | Flutter app needs all API endpoints working | Day 2 → Day 3 |
| **Shayan** | Trace endpoints needed for pipeline wiring | Day 2 |
| **All** | Web dashboard needs all backend endpoints stable | Day 4 |
