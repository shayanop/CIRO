"""In-memory alert/ticket broadcast hub for near-real-time UI updates.

Increments a monotonic version whenever alerts or tickets change so clients
can poll ``GET /simulate/alerts/version`` or subscribe to the SSE stream at
``GET /simulate/alerts/stream``.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict

_version: int = 0
_lock = asyncio.Lock()


def get_version() -> int:
    return _version


def bump() -> int:
    """Increment broadcast version; return the new value."""
    global _version
    _version += 1
    return _version


def reset() -> None:
    global _version
    _version = 0


def snapshot(alerts: list, tickets: list) -> Dict[str, Any]:
    return {
        "version": _version,
        "alerts": alerts,
        "tickets": tickets,
        "alerts_count": len(alerts),
        "tickets_count": len(tickets),
    }


async def event_stream(
    alerts_supplier,
    tickets_supplier,
    poll_interval: float = 1.0,
    max_events: int | None = None,
) -> AsyncIterator[str]:
    """Yield Server-Sent Events when the broadcast version changes."""
    last = -1
    sent = 0
    while True:
        current = get_version()
        if current != last:
            last = current
            payload = snapshot(alerts_supplier(), tickets_supplier())
            yield f"data: {json.dumps(payload, default=str)}\n\n"
            sent += 1
            if max_events is not None and sent >= max_events:
                return
        await asyncio.sleep(poll_interval)
