# CIRO API Reference

Base URL: `http://localhost:8000` (or your deployed host).

Interactive docs: **`/docs`** (Swagger UI) · **`/redoc`**

All request/response bodies are JSON unless noted. Timestamps are UTC ISO-8601.

---

## System

### `GET /health`

```json
{
  "status": "ok",
  "agents": 5,
  "version": "1.0.0",
  "system": "CIRO – Crisis Intelligence & Response Orchestrator"
}
```

### `GET /`

Returns pointers to `/docs` and `/web/index.html`.

---

## Pipeline

### `POST /pipeline/run`

Runs the full 5-agent chain on a single raw signal. Clears the ingest buffer first so prior runs do not contaminate crisis type.

**Request**

```json
{
  "source": "social",
  "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
  "metadata": { "geo": "G-10" }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source` | string | yes | `social`, `weather`, or `traffic` |
| `text` | string | yes | Urdu or English free text |
| `metadata` | object | no | Optional `geo`, `user`, etc. |

**Response** — `PipelineResult`

| Field | Description |
|-------|-------------|
| `run_id` | Trace run identifier |
| `batch` | `SignalBatch` from ingestion |
| `event` | `CrisisEvent` from detection |
| `analysis` | `CrisisAnalysis` from reasoning |
| `plan` | `ActionPlan` from planning |
| `simulation` | `SimulationResult` from simulation |
| `total_duration_ms` | Wall-clock ms for the run |

### `POST /pipeline/auto`

Scans live Pakistani weather (wttr.in) and news RSS, selects the highest-severity candidate, and runs `/pipeline/run`. May take up to ~90s if network is slow.

**Request:** empty body `{}`

**Errors:** `503` if no live signals could be built.

---

## Signal ingestion

### `POST /ingest/signal`

Normalises one raw signal and appends it to the in-memory buffer.

**Request:** same as `RawSignalInput` above.

**Response:** `SignalBatch` with `batch_id`, `signals[]` (each with `signal_id`, `language`, `location`, `severity_hint`, `keywords`, `engagement`, `metadata`).

### `POST /ingest/auto`

Pulls mock weather and traffic (and optional corroboration). Caps at **4 signals** (max 2 weather + 2 traffic). Supports `location_filter` query/body to focus corroboration (e.g. `G-10`).

### `POST /ingest/clear`

Clears the signal buffer. Returns `{"status": "cleared"}`.

---

## Event detection

### `POST /detect/crisis`

**Request**

```json
{
  "batch_id": "batch_20260519_120000_ab12",
  "signals": [ "...Signal objects..." ]
}
```

Or pass the full `SignalBatch` object returned from ingest.

**Response** — `CrisisEvent`

| Field | Type | Notes |
|-------|------|-------|
| `event_id` | string | `evt_<hex>` |
| `crisis_type` | enum | 8 types — see PIPELINE_CONTRACT |
| `location` | string | Resolved sector/road |
| `severity` | enum | `low` … `critical` |
| `confidence` | float | 0.0–1.0 |
| `contributing_signal_ids` | string[] | |
| `explanation` | string | Human-readable scoring summary |
| `escalated` | bool | Prior-event escalation flag |

---

## Reasoning

### `POST /reason/analyse`

**Request:** `CrisisEvent` JSON.

**Response** — `CrisisAnalysis`

| Field | Description |
|-------|-------------|
| `analysis_id` | `ana_<hex>` |
| `event_id` | Links to event |
| `impact` | string[] bullet points |
| `affected_population` | string estimate |
| `infrastructure_at_risk` | string[] |
| `urgency` | `immediate`, `within_hour`, `monitoring`, etc. |
| `summary` | Short narrative |

Uses **Groq** when `GROQ_API_KEY` is set; otherwise deterministic cache keyed by `(crisis_type, severity)`.

### `GET /reason/cache/stats` · `POST /reason/cache/clear`

Inspect or clear the reasoning response cache.

---

## Action planning

### `POST /plan/actions`

**Request:** `CrisisEvent` fields plus embedded `analysis` (`PlanRequest`).

**Response** — `ActionPlan`

```json
{
  "plan_id": "plan_abc123",
  "event_id": "evt_...",
  "actions": [
    { "action_type": "reroute_traffic", "parameters": { "location": "G-10" } }
  ]
}
```

Action sets depend on `(crisis_type, severity)` — e.g. flood critical → reroute, boats, alert, relief camp.

---

## Simulation

### `POST /simulate/execute`

**Request:** `ActionPlan` JSON.

**Response** — `SimulationResult` with `before`, `after`, `actions_executed`, `tickets_created`, `alerts_sent`, congestion metrics.

Side effect: bumps **alert broadcast version** for SSE/poll clients.

### `POST /simulate/reset`

Resets tickets, alerts, world state, and broadcast version.

### `GET /simulate/state`

Full in-memory world dictionary.

### `GET /simulate/tickets` · `GET /simulate/alerts`

Return **bare JSON arrays** (not wrapped in `{ "tickets": ... }`). Flutter/web clients handle both shapes.

### `GET /simulate/alerts/version`

```json
{
  "version": 3,
  "alerts": [ "...CiroAlert..." ],
  "tickets": [ "...EmergencyTicket..." ],
  "alerts_count": 2,
  "tickets_count": 1
}
```

### `GET /simulate/alerts/stream`

Server-Sent Events (`text/event-stream`). Each event:

```
data: {"version":3,"alerts":[...],"tickets":[...],...}

```

| Query | Description |
|-------|-------------|
| `once=true` | Emit one snapshot and close (useful for tests/tools) |

### `PATCH /simulate/tickets/{ticket_id}/status`

**JSON body:** `{"status": "in_progress"}`  
**Or query:** `?status=resolved`

---

## Maps

### `GET /maps/crisis-overlay`

| Query | Default | Description |
|-------|---------|-------------|
| `location` | required | e.g. `G-10`, `Shahrah-e-Faisal` |
| `crisis_type` | optional | Refines overlay file selection |

Returns GeoJSON `FeatureCollection` (pin, affected polygon, blocked/alternate routes).

### `GET /maps/static-map`

Returns a Google Static Maps URL (requires `GOOGLE_MAPS_API_KEY` in env).

### `GET /maps/routes`

Pre-defined alternate route library from `backend/data/route_library.json`.

---

## Outcome

### `GET /outcome/summary`

Before/after comparison: congestion reduction %, vehicles rerouted, min ETA, alerts dispatched, tickets created.

---

## Trace

### `GET /trace/latest`

Full latest run: `run_id`, `steps[]` (agent, step, input, output, `duration_ms`, timestamp), `status`, `outcome`.

### `GET /trace/history`

Up to **10** recent runs. Each entry includes enriched fields for the crisis feed:

`crisis_type`, `severity`, `confidence`, `location`, `analysis_summary`, `impact`, `urgency`, `steps`, etc.

---

## Mock data

| Endpoint | Returns |
|----------|---------|
| `GET /mock/social` | Normalised social signal object (`content`, `severity_hint`, `keywords`, `engagement`) |
| `GET /mock/weather` | Weather alert JSON |
| `GET /mock/traffic` | Traffic congestion JSON |

---

## Error codes

| Code | Typical cause |
|------|----------------|
| 422 | Pydantic validation failure |
| 404 | Unknown ticket id |
| 503 | `/pipeline/auto` found no live signals |

---

## Example: curl demo flood

```bash
curl -s -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"source":"social","text":"G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"}' \
  | python -m json.tool
```

---

See also: [`PIPELINE_CONTRACT.md`](PIPELINE_CONTRACT.md) for canonical schema fields.
