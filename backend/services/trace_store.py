"""In-memory trace accumulator for the CIRO agent pipeline.

Every agent endpoint calls ``trace_store.log_step()`` so the full
reasoning chain is queryable via ``/trace/latest`` and rendered on the
mobile Agent Trace screen and the web dashboard pipeline panel.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TraceStore:
    """Singleton-style in-memory store for pipeline run traces."""

    def __init__(self) -> None:
        self._runs: List[Dict[str, Any]] = []
        self._current_run: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def start_run(self, signal_text: str = "") -> str:
        """Begin a new pipeline run; returns a unique ``run_id``."""
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self._current_run = {
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "signal_text": signal_text,
            "steps": [],
            "outcome": None,
            "total_duration_ms": 0,
            "status": "running",
        }
        return run_id

    def log_step(
        self,
        run_id: str,
        agent: str,
        step: str,
        input_data: dict,
        output_data: dict,
        duration_ms: int = 0,
    ) -> None:
        """Append a step to the current (or matching) run."""
        run = self._current_run
        if run is None or run["run_id"] != run_id:
            # Fallback: look up in history
            for r in reversed(self._runs):
                if r["run_id"] == run_id:
                    run = r
                    break
            else:
                return  # unknown run_id – silently skip

        run["steps"].append(
            {
                "agent": agent,
                "step": step,
                "input": input_data,
                "output": output_data,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        run["total_duration_ms"] += duration_ms

    def complete_run(self, run_id: str, outcome: str = "") -> None:
        """Mark the current run as complete and archive it."""
        if self._current_run and self._current_run["run_id"] == run_id:
            self._current_run["status"] = "complete"
            self._current_run["outcome"] = outcome
            self._current_run["completed_at"] = datetime.now(timezone.utc).isoformat()
            self._runs.append(copy.deepcopy(self._current_run))
            self._current_run = None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Return the most-recent completed run, or the in-progress one."""
        if self._current_run:
            return self._current_run
        if self._runs:
            return self._runs[-1]
        return None

    def get_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """Return the last *n* completed run summaries."""
        summaries = []
        for run in self._runs[-n:]:
            summaries.append(
                {
                    "run_id": run["run_id"],
                    "started_at": run.get("started_at"),
                    "outcome": run.get("outcome"),
                    "total_duration_ms": run.get("total_duration_ms", 0),
                    "status": run.get("status"),
                    "steps_count": len(run.get("steps", [])),
                }
            )
        return summaries

    def reset(self) -> None:
        """Clear all trace data."""
        self._runs.clear()
        self._current_run = None


# Module-level singleton – import from here everywhere.
trace_store = TraceStore()
