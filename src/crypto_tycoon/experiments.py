"""Client-side helper for experiment assignment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import hashlib
import json
import urllib.error
import urllib.request

DEFAULT_EXPERIMENTS: List[Dict[str, object]] = [
    {
        "id": "starter_price_test",
        "active": True,
        "assignment": "weighted",
        "weights": {"A": 0.5, "B": 0.5},
        "variants": [
            {"id": "A", "price": 1.99},
            {"id": "B", "price": 3.49},
        ],
    },
    {
        "id": "dailyRewardIntensity",
        "active": True,
        "assignment": "balanced",
        "variants": [
            {"id": "soft", "multiplier": 1.0},
            {"id": "medium", "multiplier": 1.25},
            {"id": "aggressive", "multiplier": 1.75},
        ],
    },
]


@dataclass
class ExperimentAssignmentClient:
    backend_url: Optional[str] = "http://localhost:4000"

    def assign(self, player_id: str) -> Dict[str, Dict[str, object]]:
        if self.backend_url:
            try:
                request = urllib.request.Request(
                    url=f"{self.backend_url.rstrip('/')}/api/experiments/assign",
                    data=json.dumps({"playerId": player_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=3) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                assignments = payload.get("assignments")
                if assignments:
                    return assignments
            except (urllib.error.URLError, TimeoutError, ValueError):
                pass
        return self._local_assign(player_id)

    def _local_assign(self, player_id: str) -> Dict[str, Dict[str, object]]:
        assignments: Dict[str, Dict[str, object]] = {}
        for experiment in DEFAULT_EXPERIMENTS:
            if not experiment.get("active", False):
                continue
            variant = _pick_variant(player_id, experiment)
            if variant:
                assignments[experiment["id"]] = variant
        return assignments


def _pick_variant(player_id: str, experiment: Dict[str, object]) -> Optional[Dict[str, object]]:
    variants = experiment.get("variants", [])
    if not variants:
        return None
    assignment = experiment.get("assignment")
    if assignment == "weighted":
        weights: Dict[str, float] = experiment.get("weights", {})  # type: ignore[arg-type]
        roll = _hash_to_float(player_id + experiment["id"])
        cumulative = 0.0
        for variant in variants:  # type: ignore[assignment]
            vid = variant.get("id")
            cumulative += weights.get(vid, 0)
            if roll <= cumulative:
                return variant
        return variants[-1]  # type: ignore[index]
    index = _hash_to_int(player_id + experiment["id"], len(variants))
    return variants[index]  # type: ignore[index]


def _hash_to_int(seed: str, modulo: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16)
    return value % max(modulo, 1)


def _hash_to_float(seed: str) -> float:
    return _hash_to_int(seed, 10_000) / 10_000
