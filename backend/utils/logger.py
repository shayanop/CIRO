"""Structured JSON logger for CIRO agent steps.

Every agent endpoint calls `log_agent_step()` at entry/exit so the full
reasoning chain is reproducible from logs alone, independent of the
in-memory TraceStore.
"""
from datetime import datetime, timezone

import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


def log_agent_step(
    agent: str,
    step: str,
    input_data: dict,
    output_data: dict,
    duration_ms: int = 0,
) -> None:
    """Emit a single structured log line for one agent step."""
    logger.info(
        "agent_step",
        agent=agent,
        step=step,
        input=input_data,
        output=output_data,
        duration_ms=duration_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
