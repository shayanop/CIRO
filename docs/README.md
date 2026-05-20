# CIRO Documentation

| Document | Purpose |
|----------|---------|
| [Architecture.md](Architecture.md) | System layers, data flow, alert broadcast, live scanner |
| [AgentDesign.md](AgentDesign.md) | Per-agent inputs, outputs, and decision logic |
| [PIPELINE_CONTRACT.md](PIPELINE_CONTRACT.md) | Canonical JSON schemas for pipeline stages |
| [API_REFERENCE.md](API_REFERENCE.md) | HTTP endpoint reference with examples |
| [QA_METRICS.md](QA_METRICS.md) | Test counts, severity thresholds, performance targets |
| [Assumptions.md](Assumptions.md) | Mock boundaries, LLM fallbacks, demo caveats |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | 3–5 minute hackathon demo walkthrough |

**Project entry point:** [../README.md](../README.md)

**Sprint plans:** [../Plans/](../Plans/)

**Run QA matrix:**

```bash
cd backend
python -m pytest -q
python scripts/qa_report.py
```
