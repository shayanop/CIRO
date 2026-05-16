"""In-memory TTL+LRU cache for agent responses.

Keyed by arbitrary hashable tuples (e.g. ``(event_id, crisis_type, severity)``)
with a per-entry TTL.  Used by the Reasoning Agent to keep repeat-demo
latency below ~50ms.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Hashable, Optional


class TTLCache:
    """A small thread-safe LRU cache with per-entry TTL."""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 600) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: "OrderedDict[Hashable, tuple[float, Any]]" = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: Hashable) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            expires_at, value = entry
            if expires_at < time.time():
                self._store.pop(key, None)
                self._misses += 1
                return None
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time() + self.ttl_seconds, value)
            self._store.move_to_end(key)
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._store),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
            }


analysis_cache = TTLCache(max_size=256, ttl_seconds=600)
