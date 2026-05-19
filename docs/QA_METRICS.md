# CIRO Backend QA Metrics

Generated from automated tests and `backend/scripts/qa_report.py`.

## Test suite

| Metric | Value |
|--------|-------|
| Automated tests | **139+** (`pytest` in `backend/`) |
| Typical runtime | ~2 seconds (local, fallback LLM cache) |

## Pipeline performance (in-process)

| Metric | Value |
|--------|-------|
| Full `POST /pipeline/run` | **&lt; 30 ms** typical |
| Cached `POST /reason/analyse` (repeat) | **&lt; 100 ms** |
| Agents in pipeline | **5** |
| Crisis types | **8** |

## Demo scenario expectations (after scoring tune)

| Scenario | Expected severity | Expected confidence |
|----------|-------------------|---------------------|
| Urdu flood G-10 (single signal) | **high** or **critical** | **≥ 0.70** |
| English heatwave Jacobabad | **high** or **critical** | **≥ 0.70** |
| Shahrah blockage | **high** | **≥ 0.55** |
| Vague single signal | **low** | **&lt; 0.35** |
| Fire I-9 | **high** | **≥ 0.55** |
| Multi-signal buffered flood | **critical** | **≥ 0.85** |

## Real-time alerts

| Mechanism | Endpoint |
|-----------|----------|
| SSE stream | `GET /simulate/alerts/stream` |
| Version poll | `GET /simulate/alerts/version` |
| Mobile poll interval | **2 s** |
| Web | SSE with **2 s** poll fallback |

## Severity thresholds (`confidence_to_severity`)

| Confidence | Severity |
|------------|----------|
| ≥ 0.75 | critical |
| ≥ 0.55 | high |
| ≥ 0.35 | medium |
| &lt; 0.35 | low |

Run `python backend/scripts/qa_report.py` for a fresh JSON matrix.
