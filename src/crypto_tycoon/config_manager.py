"""Dynamic configuration management for Crypto Tycoon."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional
import json
import urllib.error
import urllib.parse
import urllib.request

from .experiments import DEFAULT_EXPERIMENTS

STATIC_CONFIG: Dict[str, Any] = {
    "pricing": {
        "starter_pack": 2.49,
        "rig_cost_multiplier": 1.0,
        "booster_pack": 4.99,
    },
    "boostValues": {
        "defaultMultiplier": 1.15,
        "defaultDurationSeconds": 300,
    },
    "dailyRewardScaling": {
        "base": 125,
        "multiplier": 1.0,
    },
    "prestigeThresholds": {
        "tier1": 50_000,
        "tier2": 250_000,
        "tier3": 1_000_000,
    },
    "marketSentiment": {
        "bullish": 0.35,
        "neutral": 0.4,
        "bearish": 0.25,
    },
}


class ConfigManager:
    """Resolves static, dynamic, experiment, and player overrides."""

    def __init__(
        self,
        player_id: str,
        assignments: Optional[Dict[str, Dict[str, Any]]] = None,
        backend_url: Optional[str] = "http://localhost:4000",
    ) -> None:
        self.player_id = player_id
        self.backend_url = backend_url.rstrip("/") if backend_url else None
        self.assignments = assignments or {}
        self.dynamic_overrides: Dict[str, Any] = {}
        self.player_overrides: Dict[str, Any] = {}
        self.remote_config: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Attempt to fetch the resolved config from the backend."""

        if not self.backend_url:
            self.remote_config = None
            return
        try:
            query = urllib.parse.urlencode({"playerId": self.player_id})
            with urllib.request.urlopen(f"{self.backend_url}/api/game/dynamicConfig?{query}", timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError):
            self.remote_config = None
            return
        self.assignments = payload.get("assignments", self.assignments)
        self.remote_config = payload.get("config")

    def set_assignments(self, assignments: Dict[str, Dict[str, Any]]) -> None:
        self.assignments = assignments

    def update_player_overrides(self, overrides: Dict[str, Any]) -> None:
        self.player_overrides = deep_merge({}, self.player_overrides, overrides)

    def resolve(self) -> Dict[str, Any]:
        if self.remote_config:
            return deepcopy(self.remote_config)
        return deep_merge(
            {},
            STATIC_CONFIG,
            self.dynamic_overrides,
            self._experiment_overrides(),
            self.player_overrides,
        )

    # ------------------------------------------------------------------
    def _experiment_overrides(self) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        assignments = self.assignments or {}
        for experiment in DEFAULT_EXPERIMENTS:
            variant = assignments.get(experiment["id"])
            if not variant:
                continue
            deep_merge(overrides, _variant_to_config(experiment["id"], variant))
        return overrides


def _variant_to_config(experiment_id: str, variant: Dict[str, Any]) -> Dict[str, Any]:
    if experiment_id == "starter_price_test":
        return {"pricing": {"starter_pack": variant.get("price", 2.49)}}
    if experiment_id == "dailyRewardIntensity":
        return {"dailyRewardScaling": {"multiplier": variant.get("multiplier", 1.0)}}
    if experiment_id == "booster_strength":
        return {
            "boostValues": {
                "defaultMultiplier": variant.get("boost", 1.15),
                "defaultDurationSeconds": variant.get("duration", 300),
            }
        }
    return {}


def deep_merge(base: Dict[str, Any], *extras: Dict[str, Any]) -> Dict[str, Any]:
    for extra in extras:
        for key, value in (extra or {}).items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                deep_merge(base[key], value)
            else:
                base[key] = deepcopy(value)
    return base
