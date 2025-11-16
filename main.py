"""Entry point for the Crypto Tycoon v1 game."""
from crypto_tycoon import CryptoTycoonCLI


def main() -> None:
    cli = CryptoTycoonCLI()
    cli.run()


if __name__ == "__main__":
    main()
