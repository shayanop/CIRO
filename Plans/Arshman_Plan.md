# ⚙️ Arshman – Backend Dev: Reasoning & Simulation
## Individual 5-Day Plan

> **Role**: Build the Reasoning & Situation Analysis Agent with Gemini integration, create and manage all mock data sets, implement the Alert & Ticket system, and own final documentation.

---

## Day 1 – Mock Data Factory

### Pre-Meeting (All Members)
- [ ] Join stand-up call on Google Meet
- [ ] Clone the monorepo and create feature branch: `git checkout -b feat/arshman-day1`

### Social Signals Data
- [ ] Create `/backend/data/` directory
- [ ] Create `social_signals.json` – array of 20 objects, each with `id`, `text`, `location`, `timestamp`, `language`. Include:
  - Urdu flood: "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"
  - English flood: "Flash flood happening at George Town for past 30 mins"
  - Heatwave: "It's 48 degrees in Jacobabad, people collapsing on the street"
  - Blockage: "Shahrah-e-Faisal completely jammed after truck accident"
  - Infrastructure: "Power line down on Constitution Avenue, sparks flying"
  - 15 more variations in Urdu and English across crisis types

### Weather & Traffic Data
- [ ] Create `weather_mock.json` – simulates OpenWeatherMap API: `main.temp`, `weather[0].description`, `rain.1h`, `alerts[]` with heavy rainfall and heatwave alerts
- [ ] Create `traffic_mock.json` – route objects each with: `route_id`, `name`, `congestion_level` (0–100), `status` (free/slow/blocked). Include G-10, Margalla Road, Shahrah-e-Faisal, Constitution Avenue

### Mock Router
- [ ] Write `/backend/routers/mock.py`: load each JSON file, serve via GET endpoints. Return a random entry from social signals each time

### Pydantic Models
- [ ] Write `/backend/models/signal.py` with these models:
  ```python
  class CrisisType(str, Enum):
      FLOOD = "flood"
      HEATWAVE = "heatwave"
      BLOCKAGE = "blockage"
      ACCIDENT = "accident"
      INFRASTRUCTURE = "infrastructure"
  
  class Severity(str, Enum):
      LOW = "low"
      MEDIUM = "medium"
      HIGH = "high"
      CRITICAL = "critical"
  
  class Signal(BaseModel):
      signal_id: str
      source: str          # "social"|"weather"|"traffic"
      content: str
      location: Optional[str] = None
      timestamp: datetime
      language: Optional[str] = "en"
      severity_hint: Optional[str] = None
  
  class SignalBatch(BaseModel):
      batch_id: str
      signals: List[Signal]
      primary_location: Optional[str] = None
  
  class CrisisEvent(BaseModel):
      event_id: str
      crisis_type: CrisisType
      location: str
      confidence: float     # 0.0 to 1.0
      severity: Severity
      signals: List[Signal]
      explanation: str
      detected_at: datetime
  ```

### Testing
- [ ] Test all 3 mock endpoints via Postman. Confirm valid JSON responses
- [ ] Commit: `"feat: mock data factory, 20 social signals, weather, traffic, pydantic models"`

### ✅ End of Day Deliverable
All 3 mock endpoints serving realistic data. Pydantic models complete.

---

## Day 2 – Reasoning & Situation Analysis Agent

- [ ] Open `/backend/routers/reason.py`
- [ ] Implement **POST /reason/analyse** – accepts `CrisisEvent`, returns `CrisisAnalysis`

### Antigravity / Gemini API Wrapper
- [ ] Write `/backend/services/antigravity.py`:
  ```python
  async def call_reasoning_agent(crisis_event: dict) -> dict:
      """Call Antigravity reasoning agent which uses Gemini."""
      prompt = f"""
      You are a crisis management AI for Pakistani cities.
      Given this detected crisis: {json.dumps(crisis_event)}
      
      Respond ONLY with valid JSON containing:
      {{
          "impact_bullets": ["...", "...", "..."],
          "affected_population_estimate": "...",
          "infrastructure_risk": "low|medium|high|critical",
          "recommended_urgency": "immediate|within_hour|monitoring",
          "plain_english_summary": "..."
      }}
      """
      async with httpx.AsyncClient() as client:
          response = await client.post(
              f"https://antigravity.googleapis.com/v1/projects/"
              f"{ANTIGRAVITY_PROJECT}/agents/"
              f"reasoning-analysis-agent:run",
              headers={"Authorization": f"Bearer {GEMINI_API_KEY}"},
              json={"input": prompt},
              timeout=10.0
          )
          return response.json()
  ```

### Fallback Cache
- [ ] Add Gemini response cache in `/data/gemini_cache.json` – pre-populated for all 5 demo scenarios
- [ ] If Gemini call fails, return cached response for the matching crisis type

### Registration
- [ ] Register endpoint as Antigravity tool on `reasoning-analysis-agent`
- [ ] Commit: `"feat: reasoning agent with Gemini integration and fallback cache"`

### ✅ End of Day Deliverable
Agent returns structured crisis analysis with impact bullets and urgency level.

---

## Day 3 – Alert & Emergency Ticket System

### Simulation Pydantic Models
- [ ] Create `/backend/models/simulation.py`:
  ```python
  class EmergencyTicket(BaseModel):
      ticket_id: str
      crisis_type: str
      location: str
      unit_dispatched: str    # "Rescue Boats"|"Traffic Police"|...
      eta_minutes: int
      status: str             # "open"|"dispatched"|"resolved"
      created_at: datetime
  
  class Alert(BaseModel):
      alert_id: str
      message: str
      target_area: str
      channel: str            # "push"|"sms"|"broadcast"
      sent_at: datetime
      recipients_count: int   # simulated number
  
  class SimulationResult(BaseModel):
      run_id: str
      actions_executed: List[str]
      tickets_created: List[EmergencyTicket]
      alerts_sent: List[Alert]
      routes_updated: List[dict]    # [{route, before, after}]
      state_before: dict
      state_after: dict
      estimated_congestion_reduction: float
      estimated_response_time_minutes: int
  ```

### Ticket & Alert Endpoints
- [ ] Implement **GET /simulate/tickets**: return all tickets from `system_state.active_tickets`
- [ ] Implement **GET /simulate/alerts**: return all alerts from `system_state.sent_alerts`
- [ ] Implement **PATCH /simulate/tickets/{ticket_id}/status**: update ticket status (dispatched → resolved). Used for demo progression

### Alert Service
- [ ] Write `/backend/services/alert_service.py`:
  - `send_simulated_alert()` – logs via structlog, increments simulated recipient count (50–5000 random), appends to state
- [ ] Commit: `"feat: emergency ticket and alert models, status update endpoint, alert service"`

### ✅ End of Day Deliverable
Full ticket and alert lifecycle implemented and queryable.

---

## Day 4 – Mobile App UX Polish

### Consistent Design Language (All 5 Flutter Screens)
- [ ] Consistent AppBar with CIRO logo (text logo is fine) and location subtitle
- [ ] Custom `ThemeData`: `primarySwatch` based on `Color(0xFF1A3C5E)`, `cardTheme` with rounded corners and subtle shadow
- [ ] Crisis type icons:
  - `Icons.water` (flood)
  - `Icons.wb_sunny` (heatwave)
  - `Icons.traffic` (blockage)
  - `Icons.car_crash` (accident)
- [ ] Severity colour system:
  - `Color(0xFF27AE60)` green (LOW)
  - `Color(0xFFE67E22)` amber (MEDIUM)
  - `Color(0xFFE74C3C)` red (HIGH)
  - `Color(0xFF8E44AD)` purple (CRITICAL)

### Input Screen
- [ ] Add Input Screen accessible from a FAB on the home screen
- [ ] `TextField` with multiline support and hint text in both English and Urdu
- [ ] "Submit Signal" button calling `api_service.ingestSignal(text)`
- [ ] Show `CircularProgressIndicator` during API call, then navigate to crisis result

### Edge Cases
- [ ] Add empty state widgets: when no crisis detected, show city skyline illustration with text "No active crises detected"
- [ ] Add error handling: all API calls wrapped in try-catch. On error, show `SnackBar` with "Retry" button
- [ ] Commit: `"feat: mobile UX polish, consistent theme, input screen, empty states, error handling"`

### ✅ End of Day Deliverable
App is visually polished and handles all edge cases. Demo-ready.

---

## Day 5 – Final README & Documentation + Submission

### Final README (Morning)
- [ ] Write the complete **README.md**:
  - Project Overview: 3 sentences. What CIRO does, why it matters
  - System Architecture: embed `docs/architecture.png`. Describe 5-layer pipeline
  - Google Antigravity Usage: paragraph explaining orchestration, tool integration, Gemini reasoning
  - Agent Descriptions: one paragraph per agent
  - Tools & APIs Used: table with Tool, Purpose, Mock/Live
  - Setup Instructions: step-by-step – clone, `cd backend`, `pip install -r requirements.txt`, `uvicorn main:app`, `flutter run`
  - Demo Scenarios: table with 5 scenarios, input, expected output
  - Agent Trace: link to `docs/sample_trace.json`. Screenshot of trace screen
  - Assumptions: bullet list from `ASSUMPTIONS.md`
  - Team: table with name and role
  - Demo Video: embed/link

### API Reference
- [ ] Write `/docs/API_REFERENCE.md`: document all 16+ endpoints with example request and response bodies
- [ ] Confirm all links in README work (no broken links)
- [ ] Commit: `"docs: final README complete, API reference done"`

### Demo Recording (Afternoon – All Members)
- [ ] Join Google Meet. Role: **Manage backend terminal** (show logs) during recording
- [ ] Participate in 3 recording takes
- [ ] Assist with final submission

### ✅ End of Day Deliverable
Complete, professional README renders perfectly on GitHub. Demo recorded and submitted.

---

## Dependencies & Coordination Points
| With | What | When |
|---|---|---|
| **Hasnain** | FastAPI scaffold and folder structure must be ready | Day 1 |
| **Anas** | Antigravity project ID and Gemini API key for `.env` | Day 1 → Day 2 |
| **Anas** | Simulation engine needs `SimulationResult` model from Day 3 | Day 3 |
| **Saad** | Flutter models must match Pydantic models | Day 2 → Day 3 |
| **Shayan** | Trace store needs to call `log_step()` inside agent endpoints | Day 3 |
