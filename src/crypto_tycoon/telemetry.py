"""Client-side analytics tracking with batching and gzip transport."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import gzip
import json
import threading
import time
import urllib.error
import urllib.request


class AnalyticsClient:
    def __init__(
        self,
        player_id: str,
        backend_url: str = "http://localhost:4000",
        batch_interval: float = 15.0,
    ) -> None:
        self.player_id = player_id
        self.backend_url = backend_url.rstrip("/")
        self.batch_interval = max(10.0, min(batch_interval, 20.0))
        self._queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._thread.start()
        self.opt_out = False
        self.experiments: Dict[str, Dict[str, Any]] = {}

    def set_experiments(self, assignments: Dict[str, Dict[str, Any]]) -> None:
        self.experiments = assignments or {}

    def set_opt_out(self, value: bool) -> None:
        self.opt_out = value

    def track_event(self, event_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self.opt_out:
            return
        payload = {
            "eventName": event_name,
            "metadata": metadata or {},
            "timestamp": int(time.time() * 1000),
        }
        with self._lock:
            self._queue.append(payload)

    def flush(self) -> None:
        queue_copy: List[Dict[str, Any]]
        with self._lock:
            if not self._queue:
                return
            queue_copy = list(self._queue)
            self._queue.clear()
        self._send_batch(queue_copy)

    def shutdown(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self.flush()

    # ------------------------------------------------------------------
    def _flush_loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(self.batch_interval)
            self.flush()

    def _send_batch(self, events: List[Dict[str, Any]]) -> None:
        payload = {
            "playerId": self.player_id,
            "events": events,
            "experiments": self.experiments,
            "analyticsOptOut": self.opt_out,
        }
        try:
            compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
            request = urllib.request.Request(
                url=f"{self.backend_url}/api/analytics/eventBatch",
                data=compressed,
                headers={
                    "Content-Type": "application/json",
                    "Content-Encoding": "gzip",
                },
                method="POST",
            )
            urllib.request.urlopen(request, timeout=3).read()
        except (urllib.error.URLError, TimeoutError):
            # drop batch silently to keep gameplay smooth
            return
