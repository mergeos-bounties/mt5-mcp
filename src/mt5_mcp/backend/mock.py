from typing import Any, Dict, List, Optional
from .base import BaseBackend

class MockBackend(BaseBackend):
    def __init__(self):
        self.mock_symbols = {
            "EURUSD": {
                "symbol": "EURUSD",
                "digits": 5,
                "lot_step": 0.01,
                "min_lot": 0.01,
                "max_lot": 500.0,
                "trade_mode": "full",
            },
            "BTCUSD": {
                "symbol": "BTCUSD",
                "digits": 2,
                "lot_step": 0.1,
                "min_lot": 0.1,
                "max_lot": 50.0,
                "trade_mode": "full",
            },
            "GOLD": {
                "symbol": "GOLD",
                "digits": 2,
                "lot_step": 0.01,
                "min_lot": 0.01,
                "max_lot": 100.0,
                "trade_mode": "full",
            }
        }

    async def get_account_info(self) -> Dict[str, Any]:
        return {
            "login": 123456,
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "margin_free": 10000.0,
            "currency": "USD",
            "broker": "MockBroker"
        }

    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.mock_symbols.get(symbol.upper())

    async def get_positions(self) -> List[Dict[str, Any]]:
        return []

    async def get_orders(self) -> List[Dict[str, Any]]:
        return []

    async def get_history(self, days: int) -> List[Dict[str, Any]]:
        return []
