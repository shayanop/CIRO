# CIRO – Agent Design

This document is the contract for each of the five agents in the CIRO pipeline. For every agent it specifies: input schema, output schema, tools used, decision logic, and how handoff to the next agent occurs.

All schemas are Pydantic v2 models defined in `backend/schemas/`. Agent endpoints live in `backend/routers/`. All agents call `trace_store.log_step()` at entry and exit.

---

## 1. Signal Ingestion Agent

### Input schema — `RawSignalInput`
```json
{
  "source": "social | weather | traffic",
  "text": "string (free form, Urdu or English)",
  "metadata": { "user": "string?", "geo": "string?" }
}
```

### Output schema — `SignalBatch`
```json
{
  "batch_id": "sig_<timestamp>",
  "signals": [
    {
      "signal_id": "string",
      "source": "social|weather|traffic",
      "text": "string",
      "language": "ur|en",
      "location": "G-10 | Shahrah-e-Faisal | ...",
      "severity_hint": "low|medium|high",
      "keywords": ["flood", "pani"],
      "timestamp": "ISO-8601"
    }
  ]
}
```

### Tools used
- `POST /ingest/signal` — accepts a raw signal, returns a `SignalBatch`.
- `GET /mock/social`, `GET /mock/weather`, `GET /mock/traffic` — return canned source data.

### Decision logic
1. Detect language with a unicode-block check (Urdu falls in U+0600–U+06FF).
2. Run a keyword extractor (bilingual gazetteer: `pani`/`flood`, `garmi`/`heatwave`, `jam`/`blockage`, `hadsa`/`accident`).
3. Resolve `location` by matching against a list of Pakistani sectors and named roads.
4. `severity_hint` is set from keyword intensity (`shadeed` / `severe` → high).
5. Append the normalised `Signal` to the active `SignalBatch`. A batch is flushed when ≥1 signal has been collected (the demo uses single-signal batches).

### Handoff to Event Detection
The full `SignalBatch` JSON is passed as `input.signal_batch` on the Antigravity edge.

---

## 2. Event Detection Agent

### Input schema — `SignalBatch` (from above).

### Output schema — `CrisisEvent`
```json
{
  "event_id": "evt_<timestamp>",
  "crisis_type": "FLOOD|HEATWAVE|BLOCKAGE|ACCIDENT",
  "location": "string",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "confidence": 0.0,
  "contributing_signal_ids": ["..."],
  "explanation": "string"
}
```

### Tools used
- `POST /detect/crisis`.

### Decision logic
Three heuristics, summed into a confidence score in [0, 1]:
1. **Keyword cluster** — count of crisis-keywords across signals (weight 0.4).
2. **Cross-source corroboration** — +0.25 if signals come from ≥2 distinct sources (social + weather, etc.).
3. **Traffic anomaly** — +0.2 if a traffic signal reports >2× baseline congestion at the same location.

Plus a flat +0.15 multi-source bonus and +0.10 severity boost on `high` hints.

Severity ladder:
- `confidence < 0.5` → LOW
- `0.5 ≤ c < 0.7` → MEDIUM
- `0.7 ≤ c < 0.85` → HIGH
- `c ≥ 0.85` → CRITICAL

The crisis_type is the keyword bucket with the highest count; ties broken by source priority (weather > traffic > social for floods/heatwaves; traffic > social for blockages).

### Handoff to Reasoning
`CrisisEvent` JSON passed as `input.crisis_event`. If `severity == LOW`, the workflow still proceeds (so the trace remains 5 steps) but downstream actions will be empty.

---

## 3. Reasoning & Analysis Agent

### Input schema — `CrisisEvent`.

### Output schema — `CrisisAnalysis`
```json
{
  "analysis_id": "ana_<timestamp>",
  "event_id": "evt_...",
  "impact": ["bullet 1", "bullet 2", "..."],
  "affected_population": 3200,
  "infrastructure_at_risk": ["roads", "power grid"],
  "urgency": "low|medium|high|critical",
  "summary": "1-2 sentence executive summary"
}
```

### Tools used
- `POST /reason/analyse`.
- **Gemini 1.5 Pro** via Antigravity (model invocation is configured in the workflow, not in Python).

### Decision logic
1. Build a structured prompt that includes the `CrisisEvent` and the contributing signals.
2. Ask Gemini for JSON output matching `CrisisAnalysis`. Antigravity validates the schema.
3. On Gemini failure / timeout, fall back to a cached `CrisisAnalysis` keyed by `(crisis_type, severity)` — five entries covering the demo scenarios.

### Handoff to Action Planning
`CrisisAnalysis` JSON passed as `input.analysis`.

---

## 4. Action Planning Agent

### Input schema — `{ event: CrisisEvent, analysis: CrisisAnalysis }`.

### Output schema — `ActionPlan`
```json
{
  "plan_id": "plan_<timestamp>",
  "event_id": "evt_...",
  "actions": [
    {
      "action_id": "act_1",
      "type": "reroute_traffic|dispatch_rescue_boats|send_flood_alert|open_relief_camp|...",
      "params": { "target_sector": "G-10", "asset_count": 4, "eta_minutes": 12 },
      "priority": 1
    }
  ]
}
```

### Tools used
- `POST /plan/actions`.

### Decision logic
A 2-D lookup table keyed by `(crisis_type, severity)` selects an ordered list of action types. Parameters are resolved from the analysis:
- `target_sector` ← `event.location`
- `asset_count` ← scaled by `affected_population` (e.g. one rescue boat per 800 affected, capped at 8)
- `eta_minutes` ← static per action type
- `priority` ← row order in the lookup table

If severity is LOW, the action list is empty (the simulation still runs to keep the trace 5-step).

### Handoff to Simulation
`ActionPlan` JSON passed as `input.action_plan`.

---

## 5. Simulation Engine Agent

### Input schema — `ActionPlan`.

### Output schema — `SimulationResult`
```json
{
  "run_id": "run_<timestamp>",
  "before": { "congestion_pct": 78, "open_routes": [...] },
  "after":  { "congestion_pct": 31, "open_routes": [...] },
  "tickets": [ { "id": "tic_1", "type": "rescue", "status": "DISPATCHED" } ],
  "alerts":  [ { "id": "alr_1", "channel": "sms", "recipients": 3200 } ],
  "metrics": { "congestion_reduction_pct": 60, "alerts_dispatched": 3200 }
}
```

### Tools used
- `POST /simulate/execute`.
- `GET /maps/crisis-overlay` — returns the GeoJSON used to render before/after on the map.

### Decision logic
1. Snapshot the in-memory world state as `before`.
2. For each action, apply a handler (pure function on the world state):
   - `reroute_traffic` → flip route status from blocked to open, drop congestion %.
   - `dispatch_rescue_boats` → create `EmergencyTicket` records.
   - `send_flood_alert` → create `Alert` record with recipient count.
   - `open_relief_camp` → mark camp asset as active in state.
3. Snapshot the resulting state as `after`.
4. Compute metrics from the delta.

### Handoff
`SimulationResult` is returned to the workflow; Antigravity marks the run complete. The `TraceStore` records `outcome = result.metrics`.

---

## Trace Logging Contract (applies to every agent)

Every router function wraps its body with:
```python
trace_store.log_step(
    run_id=run_id,
    agent="<agent-name>",
    step="<short-step-name>",
    input=input_dict,
    output=output_dict,
    duration_ms=elapsed_ms,
)
```
This is what powers `/trace/latest`, the mobile Agent Trace screen, and the web dashboard's pipeline status panel.
