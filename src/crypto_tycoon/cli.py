"""Terminal interface for the Crypto Tycoon v1 game."""
from __future__ import annotations

from typing import Optional
import os

from .game import CryptoTycoonGame


class CryptoTycoonCLI:
    MENU = {
        "1": "Toon status",
        "2": "Handel crypto",
        "3": "Koop mining rig",
        "4": "Versnel tijd",
        "5": "Reset spel",
        "0": "Stoppen",
    }

    def __init__(self, game: Optional[CryptoTycoonGame] = None) -> None:
        self.game = game or CryptoTycoonGame()

    def run(self) -> None:
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
                self.game.reset()
                self._pause("Spel gereset. Druk op Enter om verder te gaan.")
            elif choice == "0":
                print("\nTot ziens en succes met je crypto imperium! \U0001F389")
                break
            else:
                self._pause("Ongeldige keuze. Probeer opnieuw.")

    # ------------------------------------------------------------------
    def _render_header(self) -> None:
        snapshot = self.game.snapshot()
        print("=" * 60)
        print(f"Crypto Tycoon v1 | Dag {snapshot['day']} | Vermogen: ${snapshot['portfolio_value']}")
        print("=" * 60)

    def _render_status_block(self) -> None:
        snapshot = self.game.snapshot()
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

        self._pause("\nDruk op Enter om terug te keren naar het menu.")

    def _handle_trade(self) -> None:
        snapshot = self.game.snapshot()
        print("\nBeschikbare assets:")
        for symbol, price in snapshot["asset_prices"].items():
            print(f"- {symbol}: ${price}")
        action = input("\nTyp B om te kopen of S om te verkopen: ").strip().upper()
        symbol = input("Voer het symbool in: ").strip().upper()
        if action == "B":
            amount = self._ask_float("Hoeveel USD wil je investeren? ", minimum=1.0)
            success = self.game.buy_asset(symbol, amount)
            msg = "Transactie uitgevoerd." if success else "Kon aankoop niet uitvoeren."
            self._pause(msg)
        elif action == "S":
            coins = self._ask_float("Hoeveel coins wil je verkopen? ", minimum=0.000001)
            success = self.game.sell_asset(symbol, coins)
            msg = "Verkoop uitgevoerd." if success else "Onvoldoende coins of onbekend symbool."
            self._pause(msg)
        else:
            self._pause("Actie geannuleerd.")

    def _handle_rig_purchase(self) -> None:
        print("\nBeschikbare rigs:")
        for idx, rig in enumerate(self.game.rig_catalog):
            print(
                f"{idx + 1}. {rig.name} | Kost: ${rig.cost} | Coin: {rig.coin_symbol} | Hashrate: {rig.hash_rate} | Upkeep: ${rig.energy_cost}/dag"
            )
        choice = int(self._ask_float("\nKies een rig nummer: ", minimum=1) ) - 1
        result = self.game.buy_rig(choice)
        msg = f"{result.blueprint.name} gekocht!" if result else "Onvoldoende cash of ongeldig nummer."
        self._pause(msg)

    def _handle_time_skip(self) -> None:
        days = int(self._ask_float("Hoeveel dagen wil je overslaan? ", minimum=1, maximum=365))
        self.game.advance_days(days)
        self._pause(f"{days} dagen vooruit gesprongen. Check je portfolio!")

    # ------------------------------------------------------------------
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
