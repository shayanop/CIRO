"""CIRO Backend – FastAPI Entrypoint

Mounts all agent routers, configures CORS, and serves the health endpoint.
The web dashboard is served as static files from ``/web`` once built.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import detect, ingest, maps, mock, outcome, plan, reason, simulate, trace

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CIRO – Crisis Intelligence & Response Orchestrator",
    description=(
        "Agentic AI System for real-time urban crisis detection, reasoning, "
        "and coordinated response — powered by Google Antigravity & Gemini."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS – allow everything for hackathon demo
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount Routers
# ---------------------------------------------------------------------------

app.include_router(ingest.router)
app.include_router(detect.router)
app.include_router(reason.router)
app.include_router(plan.router)
app.include_router(simulate.router)
app.include_router(maps.router)
app.include_router(outcome.router)
app.include_router(trace.router)
app.include_router(mock.router)

# ---------------------------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------------------------


@app.get("/health", tags=["System"])
async def health_check():
    """System health check."""
    return {
        "status": "ok",
        "agents": 5,
        "version": "1.0.0",
        "system": "CIRO – Crisis Intelligence & Response Orchestrator",
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint – redirects to docs."""
    return {
        "message": "CIRO API is running. Visit /docs for Swagger UI.",
        "docs_url": "/docs",
    }
