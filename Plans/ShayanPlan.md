# 📝 Shayan – Systems Dev: Logging, Docs & Demo
## Individual 5-Day Plan

> **Role**: Build the Agent Trace & Logging System, write all documentation, wire the Antigravity pipeline, design and record the demo video, and coordinate workflow visualisation.

---

## Day 1 – Architecture Docs & Logger

### Pre-Meeting (All Members)
- [ ] Join stand-up call on Google Meet
- [ ] Clone the monorepo and create feature branch: `git checkout -b feat/shayan-day1`

### Documentation
- [ ] Create `/docs/` directory. Create files: `ARCHITECTURE.md`, `AGENT_DESIGN.md`, `ASSUMPTIONS.md`
- [ ] Write **ARCHITECTURE.md**: describe all 5 layers, data flow from raw signal to outcome, Antigravity's role
- [ ] Write **AGENT_DESIGN.md** – for each of the 5 agents document:
  - Input schema
  - Output schema
  - Tools used
  - Decision logic
  - How handoff works
- [ ] Write **ASSUMPTIONS.md**: list all simulation boundaries, mock data assumptions, API limitations

### Architecture Diagram
- [ ] Create architecture diagram in draw.io (https://app.diagrams.net):
  - Show all 5 agent boxes connected with arrows
  - Mobile app and web dashboard at sides
  - Antigravity umbrella on top
- [ ] Export as PNG to `/docs/architecture.png`

### Structured Logger
- [ ] Write `/backend/utils/logger.py`:
  ```python
  import structlog
  import json
  from datetime import datetime
  
  structlog.configure(
      processors=[
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.JSONRenderer()
      ]
  )
  logger = structlog.get_logger()
  
  def log_agent_step(agent: str, step: str,
                     input_data: dict, output_data: dict,
                     duration_ms: int = 0):
      logger.info("agent_step",
          agent=agent,
          step=step,
          input=input_data,
          output=output_data,
          duration_ms=duration_ms,
          timestamp=datetime.utcnow().isoformat()
      )
  ```

### README Draft
- [ ] Write first draft of **README.md** with project title, team names, tech stack table
- [ ] Commit: `"docs: architecture, agent design, logger, assumptions, readme draft"`

### ✅ End of Day Deliverable
Complete `/docs` folder, logger utility, architecture diagram.

---

## Day 2 – Antigravity Pipeline Wiring

### Workflow Configuration
- [ ] Open Antigravity portal → **Workflow** view
- [ ] For each agent-to-agent connection, click the arrow and configure the **data mapping schema**:
  - **Ingestion → Detection**: pass full `SignalBatch` JSON as `input.signal_batch`
  - **Detection → Reasoning**: pass `CrisisEvent` JSON as `input.crisis_event`
  - **Reasoning → Planning**: pass `CrisisAnalysis` JSON as `input.analysis`
  - **Planning → Simulation**: pass `ActionPlan` JSON as `input.action_plan`
- [ ] Set completion condition for each agent: proceed when response contains `"status": "complete"`

### Test Run
- [ ] Click **Test Run** in Antigravity → inject a sample Urdu flood signal
- [ ] Watch all 5 agents fire sequentially
- [ ] Capture the complete agent trace JSON from Antigravity's **Trace** tab
- [ ] Save to `/docs/sample_trace.json`

### Trace Store Implementation
- [ ] Write `/backend/services/trace_store.py`: in-memory list of trace steps, appended by each agent
- [ ] Implement `/backend/routers/trace.py`:
  - **GET /trace/latest** returns most recent run's full trace
  - **GET /trace/history** returns last 10 run summaries
- [ ] Commit: `"feat: antigravity graph fully wired, trace system implemented, sample trace captured"`

### ✅ End of Day Deliverable
Full 5-agent pipeline runs end-to-end in Antigravity. Trace captured.

---

## Day 3 – Agent Trace Logging System

### TraceStore Class
- [ ] Implement `/backend/services/trace_store.py` fully:
  ```python
  class TraceStore:
      # In-memory list of runs
      
      def start_run(signal_text) -> str:
          # Creates new run object with unique run_id (timestamp-based)
      
      def log_step(run_id, agent, step, input, output, duration_ms):
          # Appends step to run
      
      def complete_run(run_id, outcome):
          # Marks run as complete, moves to history
      
      def get_latest() -> dict:
          # Returns most recent run
      
      def get_history(n=10) -> list:
          # Returns last n run summaries
  ```

### Agent Integration
- [ ] Wrap every agent endpoint function body with `trace_store.log_step()` calls

### Trace Endpoints
- [ ] Implement **GET /trace/latest** returning:
  ```json
  {
    "run_id": "run_20250517_143022",
    "total_duration_ms": 842,
    "outcome": "Flood detected, rerouted, tickets created",
    "steps": [
      {
        "agent": "signal-ingestion-agent",
        "step": "normalise_signal",
        "input": {"raw": "G-10 mein pani bhar gaya ..."},
        "output": {"location": "G-10", "language": "ur", "severity_hint": "high"},
        "duration_ms": 45,
        "timestamp": "2025-05-17T14:30:22Z"
      },
      { "agent": "event-detection-agent", ... },
      { "agent": "reasoning-analysis-agent", ... },
      { "agent": "action-planning-agent", ... },
      { "agent": "simulation-agent", ... }
    ]
  }
  ```
- [ ] Implement **GET /trace/history** returning last 10 run summaries (`run_id`, `crisis_type`, `timestamp`, `outcome`, `total_ms`)
- [ ] Commit: `"feat: complete agent trace store with REST endpoints and full step logging"`

### ✅ End of Day Deliverable
Every pipeline run produces a complete queryable agent trace with timing.

---

## Day 4 – Demo Script & Recording Setup

### Demo Script
- [ ] Write final demo script in `/docs/DEMO_SCRIPT.md` with exact narration and actions for each timestamp:

| Timestamp | Action | Narration |
|---|---|---|
| 0:00–0:30 | Title card | "Urban crises are everywhere in Pakistan. G-10 floods, Karachi heatwaves, Lahore blockages. But response systems are fragmented. CIRO changes that." |
| 0:30–1:00 | Web dashboard | Type Urdu flood signal. Submit. Show signal appearing in Signal Feed panel |
| 1:00–2:00 | Antigravity pipeline | Watch each agent card light up. Narrate each agent's role as it activates |
| 2:00–2:45 | Mobile app | Show crisis feed card for the detected flood. Tap card to see full analysis with impact bullets and action plan |
| 2:45–3:30 | Map screen | Show red blocked route. Tap "Run Simulation". Watch route turn green. Show tickets and alerts populating |
| 3:30–4:00 | Home dashboard | Show before/after: "Congestion reduced 60%. Rescue boats dispatched. 3,200 users alerted." |
| 4:00–4:30 | Trace screen | Show complete 5-step reasoning chain with timings |
| 4:30–5:00 | Outro | Show team names. "CIRO: faster decisions, smarter cities." |

### OBS Studio Setup
- [ ] Download and configure OBS Studio
- [ ] Set up two scenes:
  - **Scene A**: web dashboard full-screen (1920×1080)
  - **Scene B**: phone screen mirror (via scrcpy) + web dashboard side-by-side
- [ ] Do a 2-minute test recording. Check audio levels and video quality

### Backup Media
- [ ] Prepare backup GIFs (Kap or LICEcap) of each demo scenario in case of live failures
- [ ] Commit: `"docs: complete demo script, recording setup confirmed, backup GIFs saved"`

### ✅ End of Day Deliverable
Demo script finalised. OBS configured. Recording tested. Backup media ready.

---

## Day 5 – Demo Video Recording & Final Submission

### Demo Recording (Afternoon – All Members)
- [ ] All members join Google Meet. **Roles**:
  - **Anas**: narrates
  - **Saad**: runs mobile app
  - **Hasnain**: manages web dashboard
  - **Arshman**: manages backend terminal (shows logs)
  - **Shayan**: operates OBS
- [ ] Recording setup: OBS at 1920×1080, 30fps, H.264, 6000kbps. USB mic (no laptop mic)
- [ ] **Record 3 takes**. No rushing. If a step goes wrong, reset and continue cleanly

### Video Editing
- [ ] Edit the best take (or combine two takes):
  - Add intro title card (5 seconds): "CIRO – Crisis Intelligence & Response Orchestrator | Google Antigravity Hackathon"
  - Add agent name text overlays when each agent activates
  - Add "BEFORE" / "AFTER" text overlays when simulation runs
  - Add outro title card (5 seconds): team names, GitHub link
  - Cut dead air, keep total duration **3–5 minutes**
- [ ] Use DaVinci Resolve (free) or iMovie for editing. Export as MP4 H.264 1080p

### Upload & Submit
- [ ] Upload to YouTube (Unlisted) OR Google Drive (shareable link). Verify link works incognito
- [ ] Add demo video link to `README.md`: `"## Demo Video: [Watch here](...)"`
- [ ] Final commit: `"chore: demo video uploaded, link in README, v1.0 release ready"`

### Final Checklist (Your Personal Check)
- [ ] Watch demo video end-to-end
- [ ] Confirm duration is 3–5 minutes
- [ ] Confirm audio is clear
- [ ] Confirm link works for anyone (incognito test)

### ✅ End of Day Deliverable
Demo video recorded, edited, exported, uploaded, and linked. Project submitted.

---

## Dependencies & Coordination Points
| With | What | When |
|---|---|---|
| **Anas** | Antigravity YAML config needed for pipeline wiring | Day 1 → Day 2 |
| **Hasnain** | FastAPI routers needed for trace endpoint integration | Day 2 → Day 3 |
| **All agents** | Each agent endpoint must call `trace_store.log_step()` | Day 3 |
| **All** | Everyone must be available for demo recording | Day 5 afternoon |
| **Saad** | Screenshots needed for demo backup | Day 4 → Day 5 |
