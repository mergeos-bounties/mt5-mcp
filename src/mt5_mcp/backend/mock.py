"""Offline MetaTrader 5-style mock terminal (positions + pending orders)."""

from __future__ import annotations

import time
from copy import deepcopy
from typing import Any


class MockBackend:
    name = "mock"

    def __init__(self) -> None:
        self._ticket = 200000
        self.seed_demo()

    def _next_ticket(self) -> int:
        self._ticket += 1
        return self._ticket

    def seed_demo(self) -> dict[str, Any]:
        self._balance = 25_000.0
        self._credit = 0.0
        self._currency = "USD"
        self._leverage = 200
        self._login = 5005001
        self._server = "MockMT5-Demo"
        self._trade_mode = "hedging"
        self._symbols: dict[str, dict[str, Any]] = {
            "EURUSD": {
                "symbol": "EURUSD",
                "digits": 5,
                "point": 0.00001,
                "trade_contract_size": 100000,
                "bid": 1.08515,
                "ask": 1.08535,
                "last": 1.08525,
                "spread": 20,
            },
            "GBPUSD": {
                "symbol": "GBPUSD",
                "digits": 5,
                "point": 0.00001,
                "trade_contract_size": 100000,
                "bid": 1.26490,
                "ask": 1.26515,
                "last": 1.26500,
                "spread": 25,
            },
            "USDJPY": {
                "symbol": "USDJPY",
                "digits": 3,
                "point": 0.001,
                "trade_contract_size": 100000,
                "bid": 149.510,
                "ask": 149.535,
                "last": 149.520,
                "spread": 25,
            },
            "XAUUSD": {
                "symbol": "XAUUSD",
                "digits": 2,
                "point": 0.01,
                "trade_contract_size": 100,
                "bid": 2324.10,
                "ask": 2324.50,
                "last": 2324.30,
                "spread": 40,
            },
            "BTCUSD": {
                "symbol": "BTCUSD",
                "digits": 2,
                "point": 0.01,
                "trade_contract_size": 1,
                "bid": 67500.0,
                "ask": 67550.0,
                "last": 67525.0,
                "spread": 5000,
            },
        }
        self._positions: dict[int, dict[str, Any]] = {}
        self._orders: dict[int, dict[str, Any]] = {}
        self._deals: list[dict[str, Any]] = [
            {
                "ticket": 200001,
                "position_id": 200001,
                "symbol": "EURUSD",
                "side": "buy",
                "volume": 0.20,
                "price": 1.08100,
                "profit": 42.0,
                "entry": "out",
                "time": time.time() - 3600,
                "comment": "demo-deal",
            }
        ]
        self._recalc()
        return {
            "ok": True,
            "mode": "mock",
            "login": self._login,
            "trade_mode": self._trade_mode,
            "symbols": list(self._symbols),
            "positions": 0,
        }

    def _recalc(self) -> None:
        floating = sum(float(p.get("profit", 0.0)) for p in self._positions.values())
        margin = sum(float(p.get("margin", 0.0)) for p in self._positions.values())
        self._margin = round(margin, 2)
        self._equity = round(self._balance + self._credit + floating, 2)

    def doctor(self) -> dict[str, Any]:
        self._recalc()
        return {
            "ok": True,
            "mode": "mock",
            "terminal": "MetaTrader 5 (mock)",
            "connected": True,
            "login": self._login,
            "server": self._server,
            "trade_mode": self._trade_mode,
            "balance": self._balance,
            "equity": self._equity,
            "positions": len(self._positions),
            "pending_orders": len(self._orders),
            "symbols": len(self._symbols),
            "message": "Mock MT5 terminal — no MetaTrader install required",
        }

    def account(self) -> dict[str, Any]:
        self._recalc()
        return {
            "ok": True,
            "login": self._login,
            "server": self._server,
            "currency": self._currency,
            "leverage": self._leverage,
            "trade_mode": self._trade_mode,
            "balance": self._balance,
            "credit": self._credit,
            "equity": self._equity,
            "margin": self._margin,
            "margin_free": round(self._equity - self._margin, 2),
            "positions": len(self._positions),
            "pending_orders": len(self._orders),
        }

    def symbols(self) -> list[dict[str, Any]]:
        return [deepcopy(v) for v in self._symbols.values()]

    def quote(self, symbol: str) -> dict[str, Any]:
        s = self._symbols.get(symbol.upper())
        if not s:
            return {"ok": False, "error": f"unknown symbol {symbol}"}
        mid = (s["bid"] + s["ask"]) / 2
        s["bid"] = round(mid - s["point"] * 10, s["digits"])
        s["ask"] = round(mid + s["point"] * 10, s["digits"])
        s["last"] = round(mid, s["digits"])
        return {"ok": True, **deepcopy(s), "time": time.time()}

    def positions(self) -> list[dict[str, Any]]:
        self._mark_to_market()
        return [deepcopy(p) for p in self._positions.values()]

    def orders(self) -> list[dict[str, Any]]:
        return [deepcopy(o) for o in self._orders.values()]

    def _mark_to_market(self) -> None:
        for p in self._positions.values():
            q = self._symbols[p["symbol"]]
            price = q["bid"] if p["side"] == "buy" else q["ask"]
            if p["symbol"] == "BTCUSD":
                pip_value = p["volume"]
            elif p["symbol"] == "XAUUSD":
                pip_value = p["volume"] * 100
            elif p["symbol"] == "USDJPY":
                pip_value = p["volume"] * 1000 / max(price, 1)
            else:
                pip_value = p["volume"] * 100000
            direction = 1 if p["side"] == "buy" else -1
            p["profit"] = round(direction * (price - p["price_open"]) * pip_value, 2)
            p["price_current"] = price
        self._recalc()

    def order_send(
        self,
        symbol: str,
        side: str,
        volume: float,
        order_type: str = "market",
        price: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        comment: str = "",
    ) -> dict[str, Any]:
        sym = symbol.upper()
        if sym not in self._symbols:
            return {"ok": False, "error": f"unknown symbol {symbol}"}
        side_l = side.strip().lower()
        if side_l not in {"buy", "sell"}:
            return {"ok": False, "error": "side must be buy or sell"}
        if volume <= 0:
            return {"ok": False, "error": "volume must be > 0"}
        ot = (order_type or "market").strip().lower()
        q = self._symbols[sym]
        ticket = self._next_ticket()
        if ot == "market":
            open_price = q["ask"] if side_l == "buy" else q["bid"]
            margin = round(volume * 500 / max(1, self._leverage / 50), 2)
            pos = {
                "ticket": ticket,
                "symbol": sym,
                "side": side_l,
                "volume": float(volume),
                "price_open": open_price,
                "sl": sl,
                "tp": tp,
                "profit": 0.0,
                "margin": margin,
                "comment": comment or "mt5-mcp",
                "time": time.time(),
                "magic": 0,
            }
            self._positions[ticket] = pos
            deal = {
                "ticket": self._next_ticket(),
                "position_id": ticket,
                "symbol": sym,
                "side": side_l,
                "volume": float(volume),
                "price": open_price,
                "profit": 0.0,
                "entry": "in",
                "time": time.time(),
                "comment": comment or "mt5-mcp",
            }
            self._deals.insert(0, deal)
            self._mark_to_market()
            return {"ok": True, "retcode": 10009, "ticket": ticket, "position": deepcopy(pos)}
        if price is None:
            return {"ok": False, "error": "pending order requires price"}
        if ot not in {"buy_limit", "sell_limit", "buy_stop", "sell_stop"}:
            return {"ok": False, "error": f"unsupported order_type {order_type}"}
        order = {
            "ticket": ticket,
            "symbol": sym,
            "side": side_l,
            "volume": float(volume),
            "type": ot,
            "price_open": float(price),
            "sl": sl,
            "tp": tp,
            "comment": comment or "mt5-mcp",
            "time_setup": time.time(),
        }
        self._orders[ticket] = order
        return {"ok": True, "retcode": 10009, "ticket": ticket, "order": deepcopy(order)}

    def position_close(self, ticket: int, volume: float | None = None) -> dict[str, Any]:
        p = self._positions.get(int(ticket))
        if not p:
            return {"ok": False, "error": f"position {ticket} not found"}
        self._mark_to_market()
        close_vol = float(volume) if volume is not None else float(p["volume"])
        if close_vol <= 0 or close_vol > p["volume"] + 1e-9:
            return {"ok": False, "error": "invalid close volume"}
        q = self._symbols[p["symbol"]]
        close_price = q["bid"] if p["side"] == "buy" else q["ask"]
        ratio = close_vol / p["volume"]
        profit = round(float(p["profit"]) * ratio, 2)
        self._balance = round(self._balance + profit, 2)
        deal = {
            "ticket": self._next_ticket(),
            "position_id": p["ticket"],
            "symbol": p["symbol"],
            "side": "sell" if p["side"] == "buy" else "buy",
            "volume": close_vol,
            "price": close_price,
            "profit": profit,
            "entry": "out",
            "time": time.time(),
            "comment": p.get("comment", ""),
        }
        self._deals.insert(0, deal)
        if abs(close_vol - p["volume"]) < 1e-9:
            del self._positions[int(ticket)]
        else:
            p["volume"] = round(p["volume"] - close_vol, 2)
            p["margin"] = round(float(p["margin"]) * (1 - ratio), 2)
        self._recalc()
        return {"ok": True, "deal": deal, "balance": self._balance}

    def order_cancel(self, ticket: int) -> dict[str, Any]:
        o = self._orders.pop(int(ticket), None)
        if not o:
            return {"ok": False, "error": f"pending order {ticket} not found"}
        return {"ok": True, "cancelled": o}

    def history_deals(self, limit: int = 20) -> list[dict[str, Any]]:
        n = max(1, min(int(limit), 100))
        return [deepcopy(d) for d in self._deals[:n]]
