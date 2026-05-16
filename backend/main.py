"""CIRO backend entrypoint.

Run with:
    uvicorn backend.main:app --reload
"""
from fastapi import FastAPI

app = FastAPI(
    title="CIRO – Crisis Intelligence & Response Orchestrator",
    version="0.1.0",
    description="5-agent pipeline backend powered by Google Antigravity.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ciro-backend"}
