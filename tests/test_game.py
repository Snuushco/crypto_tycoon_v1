import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from crypto_tycoon.game import CryptoTycoonGame


class CryptoTycoonGameTest(unittest.TestCase):
    def setUp(self) -> None:
        self.game = CryptoTycoonGame(seed=42)

    def test_buy_asset_reduces_cash_and_increases_holdings(self) -> None:
        starting_cash = self.game.state.cash
        self.assertTrue(self.game.buy_asset("BTC", 1000))
        self.assertLess(self.game.state.cash, starting_cash)
        self.assertGreater(self.game.state.portfolio["BTC"], 0)

    def test_sell_asset_increases_cash(self) -> None:
        self.game.buy_asset("ETH", 1000)
        coins_owned = self.game.state.portfolio["ETH"]
        self.assertTrue(self.game.sell_asset("ETH", coins_owned / 2))
        self.assertGreater(self.game.state.cash, 0)

    def test_advance_days_updates_day_counter(self) -> None:
        self.game.advance_days(3)
        self.assertEqual(self.game.state.day, 3)

    def test_buy_rig_adds_owned_rig(self) -> None:
        rig = self.game.buy_rig(0)
        self.assertIsNotNone(rig)
        self.assertEqual(len(self.game.state.rigs), 1)


if __name__ == "__main__":
    unittest.main()
