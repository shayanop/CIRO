# 🔧 Anas – Lead Engineer: Antigravity & Signal Ingestion
## Individual 5-Day Plan

> **Role**: Own the Google Antigravity configuration, agent graph definition, tool-calling setup, and Signal Ingestion Agent. Drive integration testing.

---

## Day 1 – Google Antigravity Setup

### Pre-Meeting (All Members)
- [ ] Host stand-up call on Google Meet (30 min) – review challenge requirements, confirm roles
- [ ] Create GitHub organisation `ciro-hackathon`, invite all 5 members
- [ ] Create monorepo `ciro-system` with folders: `/backend`, `/mobile`, `/web`, `/docs`
- [ ] Everyone clones the repo
- [ ] Create feature branch: `git checkout -b feat/anas-day1`

### Antigravity Setup (Main Tasks)
- [ ] Navigate to the Google Antigravity portal (hackathon-provided URL). Log in with team Google account
- [ ] Click **"New Project"** → enter project name: `CIRO-AgentSystem`. Click Create. Copy and save the Project ID
- [ ] Create **5 agents** in the Agents section:
  - `signal-ingestion-agent` | Role: Ingest and normalise raw signals
  - `event-detection-agent` | Role: Detect crisis type and confidence
  - `reasoning-analysis-agent` | Role: Analyse situation using Gemini
  - `action-planning-agent` | Role: Generate coordinated response actions
  - `simulation-agent` | Role: Execute and record action simulation
- [ ] Click **Workflow tab** → drag agents onto canvas in order. Draw arrows: Ingestion → Detection → Reasoning → Planning → Simulation
- [ ] Click **Tools** → "+ Add Tool" → choose HTTP Tool. Register three tools:
  - `weather-api-tool`: GET `http://localhost:8000/mock/weather`
  - `traffic-api-tool`: GET `http://localhost:8000/mock/traffic`
  - `social-feed-tool`: GET `http://localhost:8000/mock/social`
- [ ] Assign all 3 tools to `signal-ingestion-agent`
- [ ] Click **Export** → save YAML config to `/docs/antigravity-config.yaml`
- [ ] Create `/backend/.env` with: `ANTIGRAVITY_PROJECT_ID=...` and `GEMINI_API_KEY=...`
- [ ] Commit and push: `git add . && git commit -m "feat: antigravity project and agents scaffold" && git push origin feat/anas-day1`

### ✅ End of Day Deliverable
Antigravity project live, 5 agents created, workflow graph drawn, tools registered.

---

## Day 2 – Signal Ingestion Agent

- [ ] Pull latest main: `git pull origin main && git checkout -b feat/anas-day2`
- [ ] Open `/backend/routers/ingest.py`. Replace stub with full implementation
- [ ] Implement **POST /ingest/signal** accepting JSON body: `{"raw_text": "...", "source": "social"}` or structured weather/traffic JSON

### Language Detection Function
- [ ] Define Urdu keyword list: `["mein", "gaya", "hai", "gaari", "pani", "phans", "bhar", "raha", "hua"]`
- [ ] If ≥2 Urdu keywords found → `language = "ur"`, else `language = "en"`

### Location Extractor
- [ ] Regex patterns for Pakistani sectors: `r"[GFEI]-\d+"`
- [ ] Named location list: `["George Town", "Karachi", "Lahore", "Islamabad", "Shahrah-e-Faisal", "Blue Area", "Margalla"]`
- [ ] Return first match found in text

### Severity Keyword Tagger
- [ ] HIGH keywords: `["flash flood", "pani bhar", "phans gayi", "accident", "collapse", "fire"]`
- [ ] MEDIUM keywords: `["blocked", "slow", "congestion", "delay", "jam"]`
- [ ] LOW keywords: `["rain", "traffic", "waterlogging"]`

### Signal Aggregator
- [ ] Store last 5 signals in an in-memory list. Return a `SignalBatch` combining them
- [ ] Register `normalise-signal-tool` in Antigravity portal on `signal-ingestion-agent`

### Testing
- [ ] Write `tests/test_ingest.py`: test Urdu input, English input, mixed source batch
- [ ] Run tests: `python -m pytest tests/test_ingest.py -v`
- [ ] Commit: `"feat: signal ingestion agent – language detection, location extract, severity tagging"`

### ✅ End of Day Deliverable
Agent handles bilingual input, returns clean `SignalBatch` objects.

---

## Day 3 – Action Simulation Engine

- [ ] Open `/backend/routers/simulate.py`. Implement **POST /simulate/execute**
- [ ] Create **MockSystemState** as a global in-memory object:
  ```python
  @dataclass
  class MockSystemState:
      traffic_routes: Dict[str, int] = field(default_factory=lambda: {
          "G-10 to Blue Area": 85,
          "Shahrah-e-Faisal": 90,
          "Margalla Road": 20,
          "IJP Road": 30,
          "Constitution Avenue": 40
      })
      active_tickets: List[dict] = field(default_factory=list)
      sent_alerts: List[dict] = field(default_factory=list)
      open_resources: List[str] = field(default_factory=list)
  ```

### Simulation Handlers
- [ ] `reroute_traffic`: Find route with highest congestion → set to 15. Record before/after
- [ ] `dispatch_rescue_boats`: Create `EmergencyTicket` with random ID, ETA 5–15 min
- [ ] `dispatch_traffic_police`: Create ticket with unit="Traffic Police"
- [ ] `dispatch_ambulance`: Create ticket with unit="Rescue 1122"
- [ ] `send_alert`: Create Alert object, simulate FCM push, append to state
- [ ] `open_cooling_centre`: Append "Cooling Centre G-9" to `open_resources`

### State Endpoints
- [ ] Implement before/after snapshot: capture `system_state` dict before actions, run all actions, capture after
- [ ] Expose **GET /simulate/state** returning current mock system state
- [ ] Add **POST /simulate/reset** to reset state to defaults (for demo resets)
- [ ] Commit: `"feat: full simulation engine with 6 action types and state tracking"`

### ✅ End of Day Deliverable
All action types simulate correctly with measurable before/after state change.

---

## Day 4 – Outcome Visualisation

### Backend Endpoint
- [ ] Implement **GET /outcome/summary** endpoint:
  - Compare `state_before` and `state_after` from last simulation run
  - Compute: `congestion_reduction_pct = (avg_before - avg_after) / avg_before * 100`
  - Count: `vehicles_rerouted` = simulated 200–800 (based on congestion level)
  - Fetch: `min_eta_minutes` from tickets list
  - Count: `alerts_dispatched` from alerts list
  - Return `OutcomeSummary` JSON

### Flutter Command Dashboard (`home_screen.dart`)
- [ ] Top section: large crisis type banner (colour coded by severity), location subtitle, confidence progress bar
- [ ] Middle section — 2-column layout:
  - **Left column – BEFORE**: congestion icon (red), route status "BLOCKED", alerts: 0, tickets: 0
  - **Right column – AFTER**: congestion icon (green), route status "REROUTED", alert count badge, ticket count badge
- [ ] Bottom row: 3 impact metric chips: "Congestion -{pct}%", "ETA {min} min", "Alerts: {n}"
- [ ] Animated transition: `AnimatedContainer` from BEFORE to AFTER when simulation runs
- [ ] Connect dashboard to `ciro_provider.dart`: provider holds `OutcomeSummary` state
- [ ] Commit: `"feat: outcome summary endpoint, before/after dashboard, animated state transition"`

### ✅ End of Day Deliverable
Dashboard shows quantified impact. Animation is smooth and compelling.

---

## Day 5 – Full System Integration & Submission

### Integration (Morning)
- [ ] Merge all branches to `main`: `git pull origin main`. Resolve any merge conflicts
- [ ] Start full stack: backend server + Flutter (on emulator AND physical device)
- [ ] Run all 5 E2E test scenarios. Verify 100% pass rate
- [ ] Fix any integration breakages: API URL mismatches, CORS errors, schema mismatches
- [ ] Verify Antigravity pipeline fires correctly with the live backend
- [ ] Stress test: submit 10 signals rapidly. Verify no crashes or corrupted state
- [ ] Tag release: `git tag v1.0-demo && git push --tags`

### Demo Recording (Afternoon – All Members)
- [ ] Join Google Meet. Role: **Narrate** during recording
- [ ] Participate in 3 recording takes
- [ ] Assist with final submission

### ✅ End of Day Deliverable
Stable integrated system, all tests passing, tagged release, demo recorded and submitted.

---

## Dependencies & Coordination Points
| With | What | When |
|---|---|---|
| **Hasnain** | FastAPI scaffold must be ready before agent endpoints | Day 1 → Day 2 |
| **Arshman** | Mock data endpoints needed for ingestion agent testing | Day 1 → Day 2 |
| **Shayan** | Antigravity YAML config needed for pipeline wiring | Day 1 → Day 2 |
| **Saad** | Flutter provider needs `OutcomeSummary` model | Day 4 |
| **All** | Merge and integration testing | Day 5 |
