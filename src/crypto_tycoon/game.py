"""Core simulation logic for the Crypto Tycoon v1 game."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import math
import random

from .config_manager import ConfigManager
from .telemetry import AnalyticsClient


@dataclass
class CryptoAsset:
    """Represents a tradable cryptocurrency in the game."""

    name: str
    symbol: str
    price: float
    volatility: float
    trend: float = 0.0

    def apply_market_move(self, rng: random.Random, drift_bias: float = 0.0) -> None:
        """Random walk with drift, influenced by market sentiment."""

        drift = (self.trend + drift_bias) * 0.01
        shock = rng.gauss(0, self.volatility)
        change = math.exp(drift + shock) - 1
        self.price = max(0.5, round(self.price * (1 + change), 2))


@dataclass
class MiningRigBlueprint:
    """Static blueprint used when purchasing mining rigs."""

    name: str
    cost: float
    coin_symbol: str
    hash_rate: float
    energy_cost: float

    def price_with_multiplier(self, multiplier: float) -> float:
        return round(self.cost * multiplier, 2)


@dataclass
class OwnedRig:
    """Runtime representation of a rig owned by the player."""

    blueprint: MiningRigBlueprint
    efficiency: float = 1.0

    def daily_output(self) -> float:
        base_rate = 0.00005
        return self.blueprint.hash_rate * base_rate * self.efficiency

    def upkeep_cost(self) -> float:
        return self.blueprint.energy_cost


@dataclass
class GameState:
    day: int = 0
    cash: float = 2_500.0
    portfolio: Dict[str, float] = field(default_factory=dict)
    rigs: List[OwnedRig] = field(default_factory=list)
    player_id: str = "guest"
    assigned_experiments: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    analytics_opt_out: bool = False

    def clone(self) -> "GameState":
        return GameState(
            day=self.day,
            cash=round(self.cash, 2),
            portfolio={symbol: amount for symbol, amount in self.portfolio.items()},
            rigs=[OwnedRig(rig.blueprint, rig.efficiency) for rig in self.rigs],
            player_id=self.player_id,
            assigned_experiments={key: value.copy() for key, value in self.assigned_experiments.items()},
            analytics_opt_out=self.analytics_opt_out,
        )


class CryptoTycoonGame:
    """Encapsulates simulation logic, analytics hooks and live configuration."""

    def __init__(
        self,
        seed: Optional[int] = None,
        *,
        player_id: str = "guest",
        config_manager: Optional[ConfigManager] = None,
        analytics_client: Optional[AnalyticsClient] = None,
        assignments: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.player_id = player_id
        self._rng = random.Random(seed)
        self.assignments = assignments or {}
        self.config_manager = config_manager or ConfigManager(player_id=player_id, assignments=self.assignments, backend_url=None)
        self.config = self.config_manager.resolve()
        self.analytics = analytics_client
        self.state = GameState(player_id=player_id, assigned_experiments=self.assignments)
        self.assets = self._default_assets()
        self.rig_catalog = self._default_rigs()

    # ------------------------------------------------------------------
    # Configuration helpers
    def update_config(self, new_config: Optional[Dict[str, Any]] = None) -> None:
        if new_config is not None:
            self.config = new_config
            return
        self.config_manager.refresh()
        self.config = self.config_manager.resolve()

    def refresh_live_config(self) -> None:
        self.config_manager.refresh()
        self.config = self.config_manager.resolve()

    def set_analytics_opt_out(self, value: bool) -> None:
        self.state.analytics_opt_out = value
        if self.analytics:
            self.analytics.set_opt_out(value)

    # ------------------------------------------------------------------
    # Core mechanics
    def reset(self) -> None:
        self.state = GameState(
            player_id=self.player_id,
            assigned_experiments=self.assignments,
            analytics_opt_out=self.state.analytics_opt_out,
        )
        self.assets = self._default_assets()
        self.rig_catalog = self._default_rigs()
        self._track_event("session_reset", {"playerId": self.player_id})

    def advance_days(self, days: int = 1) -> None:
        days = max(1, days)
        for _ in range(days):
            self.state.day += 1
            drift_bias = self._sentiment_drift()
            for asset in self.assets.values():
                asset.apply_market_move(self._rng, drift_bias=drift_bias)
            self._process_mining_payouts()

    def _process_mining_payouts(self) -> None:
        multiplier = self.config.get("dailyRewardScaling", {}).get("multiplier", 1.0)
        for rig in list(self.state.rigs):
            asset = self.assets.get(rig.blueprint.coin_symbol)
            if not asset:
                continue
            coins_mined = rig.daily_output() * multiplier
            self.state.portfolio[asset.symbol] = self.state.portfolio.get(asset.symbol, 0.0) + coins_mined
            self.state.cash -= rig.upkeep_cost()
            if coins_mined > 0:
                self._track_event(
                    "retention_reward_claimed",
                    {
                        "rig": rig.blueprint.name,
                        "coin": asset.symbol,
                        "amount": round(coins_mined, 8),
                    },
                )
        self.state.cash = round(self.state.cash, 2)

    # ------------------------------------------------------------------
    # Trading helpers
    def buy_asset(self, symbol: str, dollars: float) -> bool:
        asset = self.assets.get(symbol.upper())
        self._track_event(
            "purchase_attempt",
            {
                "productId": f"{symbol.upper()}_asset",
                "price": round(dollars, 2),
                "hardCurrency": False,
            },
        )
        if not asset or dollars <= 0 or dollars > self.state.cash:
            return False
        coins = dollars / asset.price
        self.state.cash -= dollars
        self.state.portfolio[symbol.upper()] = self.state.portfolio.get(symbol.upper(), 0.0) + coins
        self.state.cash = round(self.state.cash, 2)
        self._track_event(
            "purchase_success",
            {
                "productId": f"{symbol.upper()}_asset",
                "price": round(dollars, 2),
                "hardCurrency": False,
            },
        )
        return True

    def sell_asset(self, symbol: str, coins: float) -> bool:
        symbol = symbol.upper()
        asset = self.assets.get(symbol)
        owned = self.state.portfolio.get(symbol, 0.0)
        if not asset or coins <= 0 or coins > owned:
            return False
        proceeds = coins * asset.price
        self.state.portfolio[symbol] = round(owned - coins, 8)
        self.state.cash += proceeds
        self.state.cash = round(self.state.cash, 2)
        self._track_event(
            "trade_executed",
            {"symbol": symbol, "coins": round(coins, 6), "proceeds": round(proceeds, 2)},
        )
        return True

    # ------------------------------------------------------------------
    # Mining helpers
    def buy_rig(self, rig_index: int) -> Optional[OwnedRig]:
        if rig_index < 0 or rig_index >= len(self.rig_catalog):
            return None
        blueprint = self.rig_catalog[rig_index]
        cost = blueprint.price_with_multiplier(self._rig_cost_multiplier())
        if cost > self.state.cash:
            return None
        self.state.cash -= cost
        owned = OwnedRig(blueprint=blueprint)
        self.state.rigs.append(owned)
        self.state.cash = round(self.state.cash, 2)
        self._track_event(
            "upgrade_performed",
            {
                "buildingId": blueprint.name,
                "level": len(self.state.rigs),
                "cost": cost,
            },
        )
        return owned

    def get_rig_price(self, index: int) -> Optional[float]:
        if index < 0 or index >= len(self.rig_catalog):
            return None
        return self.rig_catalog[index].price_with_multiplier(self._rig_cost_multiplier())

    # ------------------------------------------------------------------
    # Reporting helpers
    def portfolio_value(self) -> float:
        total = self.state.cash
        for symbol, coins in self.state.portfolio.items():
            asset = self.assets.get(symbol)
            if asset:
                total += coins * asset.price
        return round(total, 2)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "day": self.state.day,
            "cash": self.state.cash,
            "portfolio": {symbol: round(amount, 6) for symbol, amount in self.state.portfolio.items() if amount > 0},
            "portfolio_value": self.portfolio_value(),
            "rigs": [rig.blueprint.name for rig in self.state.rigs],
            "asset_prices": {symbol: asset.price for symbol, asset in self.assets.items()},
            "experiments": self.state.assigned_experiments,
            "analyticsOptOut": self.state.analytics_opt_out,
            "config": {
                "pricing": self.config.get("pricing", {}),
                "dailyRewardScaling": self.config.get("dailyRewardScaling", {}),
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    def _default_assets(self) -> Dict[str, CryptoAsset]:
        return {
            "BTC": CryptoAsset("Bitcoin", "BTC", price=30_000.0, volatility=0.07, trend=0.01),
            "ETH": CryptoAsset("Ethereum", "ETH", price=2_000.0, volatility=0.09, trend=0.02),
            "SOL": CryptoAsset("Solana", "SOL", price=60.0, volatility=0.12, trend=0.015),
            "DOGE": CryptoAsset("Dogecoin", "DOGE", price=0.08, volatility=0.25, trend=-0.01),
        }

    def _default_rigs(self) -> List[MiningRigBlueprint]:
        return [
            MiningRigBlueprint("Starter USB Miner", cost=500.0, coin_symbol="DOGE", hash_rate=15, energy_cost=2.0),
            MiningRigBlueprint("GPU Farm", cost=2_000.0, coin_symbol="ETH", hash_rate=150, energy_cost=15.0),
            MiningRigBlueprint("ASIC Pro", cost=5_000.0, coin_symbol="BTC", hash_rate=600, energy_cost=40.0),
        ]

    def _rig_cost_multiplier(self) -> float:
        return float(self.config.get("pricing", {}).get("rig_cost_multiplier", 1.0))

    def _sentiment_drift(self) -> float:
        sentiment = self.config.get("marketSentiment", {})
        roll = self._rng.random()
        bullish = sentiment.get("bullish", 0.33)
        neutral = sentiment.get("neutral", 0.34)
        if roll <= bullish:
            return 0.5
        if roll <= bullish + neutral:
            return 0.0
        return -0.3

    def _track_event(self, event_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self.analytics:
            self.analytics.track_event(event_name, metadata)
