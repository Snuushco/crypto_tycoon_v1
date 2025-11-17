"""Terminal interface for the Crypto Tycoon v1 game."""
from __future__ import annotations

from typing import Optional
import os
import time

from .config_manager import ConfigManager
from .experiments import ExperimentAssignmentClient
from .game import CryptoTycoonGame
from .telemetry import AnalyticsClient


class CryptoTycoonCLI:
    MENU = {
        "1": "Toon status",
        "2": "Handel crypto",
        "3": "Koop mining rig",
        "4": "Versnel tijd",
        "5": "Reset spel",
        "6": "Analytics instellingen",
        "7": "Refresh live config",
        "0": "Stoppen",
    }

    def __init__(self, backend_url: str = "http://localhost:4000") -> None:
        self.backend_url = backend_url.rstrip("/")
        self.player_id: Optional[str] = None
        self.analytics: Optional[AnalyticsClient] = None
        self.config_manager: Optional[ConfigManager] = None
        self.experiment_client = ExperimentAssignmentClient(self.backend_url)
        self.game: Optional[CryptoTycoonGame] = None
        self.session_start_ts: Optional[float] = None

    # ------------------------------------------------------------------
    def run(self) -> None:
        self._bootstrap()
        try:
            while True:
                self._clear()
                self._render_header()
                for key, label in self.MENU.items():
                    print(f" {key}. {label}")
                choice = input("\nMaak een keuze: ").strip()
                if choice == "1":
                    self._render_status_block()
                elif choice == "2":
                    self._handle_trade()
                elif choice == "3":
                    self._handle_rig_purchase()
                elif choice == "4":
                    self._handle_time_skip()
                elif choice == "5":
                    self._handle_reset()
                elif choice == "6":
                    self._handle_analytics_settings()
                elif choice == "7":
                    self._handle_refresh_config()
                elif choice == "0":
                    print("\nTot ziens en succes met je crypto imperium! \U0001F389")
                    break
                else:
                    self._pause("Ongeldige keuze. Probeer opnieuw.")
        finally:
            self._shutdown()

    # ------------------------------------------------------------------
    def _bootstrap(self) -> None:
        self.player_id = self._ask_player_id()
        assignments = self.experiment_client.assign(self.player_id)
        self.config_manager = ConfigManager(player_id=self.player_id, assignments=assignments, backend_url=self.backend_url)
        self.config_manager.refresh()
        self.analytics = AnalyticsClient(player_id=self.player_id, backend_url=self.backend_url)
        self.analytics.set_experiments(assignments)
        self.game = CryptoTycoonGame(
            player_id=self.player_id,
            config_manager=self.config_manager,
            analytics_client=self.analytics,
            assignments=assignments,
        )
        self.game.update_config(self.config_manager.resolve())
        self.session_start_ts = time.time()
        self._track_session_event(
            "session_start",
            {
                "device": os.getenv("TERM", "unknown"),
                "version": "v1",
            },
        )

    def _shutdown(self) -> None:
        if self.analytics and self.session_start_ts:
            duration = int(time.time() - self.session_start_ts)
            self.analytics.track_event("session_end", {"duration": duration})
        if self.analytics:
            self.analytics.shutdown()

    # ------------------------------------------------------------------
    def _render_header(self) -> None:
        snapshot = self._game.snapshot()
        print("=" * 70)
        print(
            f"Crypto Tycoon v1 | Speler {self.player_id} | Dag {snapshot['day']} | Vermogen: ${snapshot['portfolio_value']}"
        )
        print("=" * 70)

    def _render_status_block(self) -> None:
        snapshot = self._game.snapshot()
        print("\n-- Cash --")
        print(f"${snapshot['cash']}")

        print("\n-- Portefeuille --")
        if snapshot["portfolio"]:
            for symbol, coins in snapshot["portfolio"].items():
                price = snapshot["asset_prices"][symbol]
                value = round(coins * price, 2)
                print(f"{symbol}: {coins:.6f} ({value:.2f} USD)")
        else:
            print("Nog geen coins. Handel of ga minen!")

        print("\n-- Mining Rigs --")
        if snapshot["rigs"]:
            for idx, rig in enumerate(snapshot["rigs"], start=1):
                print(f"{idx}. {rig}")
        else:
            print("Geen rigs gekocht.")

        print("\n-- Marktprijzen --")
        for symbol, price in snapshot["asset_prices"].items():
            print(f"{symbol}: ${price}")

        print("\n-- Experiments --")
        experiments = snapshot.get("experiments", {})
        if experiments:
            for exp_id, variant in experiments.items():
                label = variant.get("id") if isinstance(variant, dict) else variant
                print(f"{exp_id}: {label}")
        else:
            print("Geen experimenten toegewezen.")

        print("\n-- Config snippet --")
        pricing = snapshot["config"].get("pricing", {})
        rewards = snapshot["config"].get("dailyRewardScaling", {})
        print(f"Starter pack: ${pricing.get('starter_pack', 'n/a')} | Rig multiplier: {pricing.get('rig_cost_multiplier', 1.0)}")
        print(f"Reward multiplier: {rewards.get('multiplier', 1.0)}x")

        self._pause("\nDruk op Enter om terug te keren naar het menu.")

    def _handle_trade(self) -> None:
        snapshot = self._game.snapshot()
        self._track_session_event("shop_open", {"source": "main_menu"})
        print("\nBeschikbare assets:")
        for symbol, price in snapshot["asset_prices"].items():
            print(f"- {symbol}: ${price}")
        action = input("\nTyp B om te kopen of S om te verkopen: ").strip().upper()
        symbol = input("Voer het symbool in: ").strip().upper()
        if action == "B":
            amount = self._ask_float("Hoeveel USD wil je investeren? ", minimum=1.0)
            success = self._game.buy_asset(symbol, amount)
            msg = "Transactie uitgevoerd." if success else "Kon aankoop niet uitvoeren."
            self._pause(msg)
        elif action == "S":
            coins = self._ask_float("Hoeveel coins wil je verkopen? ", minimum=0.000001)
            success = self._game.sell_asset(symbol, coins)
            msg = "Verkoop uitgevoerd." if success else "Onvoldoende coins of onbekend symbool."
            self._pause(msg)
        else:
            self._pause("Actie geannuleerd.")

    def _handle_rig_purchase(self) -> None:
        print("\nBeschikbare rigs:")
        for idx, rig in enumerate(self._game.rig_catalog):
            price = self._game.get_rig_price(idx)
            print(
                f"{idx + 1}. {rig.name} | Kost: ${price} | Coin: {rig.coin_symbol} | Hashrate: {rig.hash_rate} | Upkeep: ${rig.energy_cost}/dag"
            )
        choice = int(self._ask_float("\nKies een rig nummer: ", minimum=1)) - 1
        result = self._game.buy_rig(choice)
        msg = f"{result.blueprint.name} gekocht!" if result else "Onvoldoende cash of ongeldig nummer."
        self._pause(msg)

    def _handle_time_skip(self) -> None:
        days = int(self._ask_float("Hoeveel dagen wil je overslaan? ", minimum=1, maximum=365))
        self._game.advance_days(days)
        self._pause(f"{days} dagen vooruit gesprongen. Check je portfolio!")

    def _handle_reset(self) -> None:
        self._game.reset()
        self._pause("Spel gereset. Druk op Enter om verder te gaan.")

    def _handle_analytics_settings(self) -> None:
        current = self._game.state.analytics_opt_out
        print("\nAnalytics opt-out staat op:", "AAN" if current else "UIT")
        toggle = input("Wil je dit toggelen? (y/N): ").strip().lower()
        if toggle == "y":
            self._game.set_analytics_opt_out(not current)
            state = "uit" if current else "aan"
            self._pause(f"Analytics tracking staat nu {state}.")
        else:
            self._pause("Geen wijziging doorgevoerd.")

    def _handle_refresh_config(self) -> None:
        self._game.refresh_live_config()
        self._pause("Config opgehaald en toegepast.")

    # ------------------------------------------------------------------
    def _ask_player_id(self) -> str:
        raw = input("Voer spelersnaam of ID in (default: guest): ").strip() or "guest"
        return raw

    def _ask_float(self, prompt: str, minimum: float, maximum: Optional[float] = None) -> float:
        while True:
            raw = input(prompt).strip()
            try:
                value = float(raw)
            except ValueError:
                print("Voer een geldig getal in.")
                continue
            if value < minimum:
                print(f"Waarde moet minimaal {minimum} zijn.")
                continue
            if maximum is not None and value > maximum:
                print(f"Waarde moet maximaal {maximum} zijn.")
                continue
            return value

    def _pause(self, message: str) -> None:
        input(f"\n{message}")

    def _clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _track_session_event(self, name: str, metadata: Optional[dict] = None) -> None:
        if self.analytics:
            self.analytics.track_event(name, metadata)

    @property
    def _game(self) -> CryptoTycoonGame:
        if not self.game:
            raise RuntimeError("Game not initialized")
        return self.game
