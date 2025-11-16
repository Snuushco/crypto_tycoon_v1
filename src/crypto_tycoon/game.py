"""Core simulation logic for the Crypto Tycoon v1 game."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math
import random


@dataclass
class CryptoAsset:
    """Represents a tradeable cryptocurrency in the game."""

    name: str
    symbol: str
    price: float
    volatility: float
    trend: float = 0.0

    def apply_market_move(self, rng: random.Random) -> None:
        """Random walk with drift to keep gameplay dynamic."""

        drift = self.trend * 0.01
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

    def clone(self) -> "GameState":
        return GameState(
            day=self.day,
            cash=round(self.cash, 2),
            portfolio={symbol: amount for symbol, amount in self.portfolio.items()},
            rigs=[OwnedRig(rig.blueprint, rig.efficiency) for rig in self.rigs],
        )


class CryptoTycoonGame:
    """Encapsulates all simulation logic and rules."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)
        self.state = GameState()
        self.assets = self._default_assets()
        self.rig_catalog = self._default_rigs()

    # ------------------------------------------------------------------
    # Initialization helpers
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

    # ------------------------------------------------------------------
    # Core mechanics
    def reset(self) -> None:
        self.state = GameState()
        self.assets = self._default_assets()

    def advance_days(self, days: int = 1) -> None:
        days = max(1, days)
        for _ in range(days):
            self.state.day += 1
            for asset in self.assets.values():
                asset.apply_market_move(self._rng)
            self._process_mining_payouts()

    def _process_mining_payouts(self) -> None:
        for rig in list(self.state.rigs):
            asset = self.assets.get(rig.blueprint.coin_symbol)
            if not asset:
                continue
            coins_mined = rig.daily_output()
            self.state.portfolio[asset.symbol] = self.state.portfolio.get(asset.symbol, 0.0) + coins_mined
            self.state.cash -= rig.upkeep_cost()
        self.state.cash = round(self.state.cash, 2)

    # ------------------------------------------------------------------
    # Trading helpers
    def buy_asset(self, symbol: str, dollars: float) -> bool:
        asset = self.assets.get(symbol.upper())
        if not asset or dollars <= 0:
            return False
        if dollars > self.state.cash:
            return False
        coins = dollars / asset.price
        self.state.cash -= dollars
        self.state.portfolio[symbol.upper()] = self.state.portfolio.get(symbol.upper(), 0.0) + coins
        self.state.cash = round(self.state.cash, 2)
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
        return True

    # ------------------------------------------------------------------
    # Mining helpers
    def buy_rig(self, rig_index: int) -> Optional[OwnedRig]:
        if rig_index < 0 or rig_index >= len(self.rig_catalog):
            return None
        blueprint = self.rig_catalog[rig_index]
        if blueprint.cost > self.state.cash:
            return None
        self.state.cash -= blueprint.cost
        owned = OwnedRig(blueprint=blueprint)
        self.state.rigs.append(owned)
        self.state.cash = round(self.state.cash, 2)
        return owned

    # ------------------------------------------------------------------
    # Reporting helpers
    def portfolio_value(self) -> float:
        total = self.state.cash
        for symbol, coins in self.state.portfolio.items():
            asset = self.assets.get(symbol)
            if asset:
                total += coins * asset.price
        return round(total, 2)

    def snapshot(self) -> Dict[str, object]:
        return {
            "day": self.state.day,
            "cash": self.state.cash,
            "portfolio": {symbol: round(amount, 6) for symbol, amount in self.state.portfolio.items() if amount > 0},
            "portfolio_value": self.portfolio_value(),
            "rigs": [rig.blueprint.name for rig in self.state.rigs],
            "asset_prices": {symbol: asset.price for symbol, asset in self.assets.items()},
        }
