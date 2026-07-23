"""Offline MetaTrader 5-style mock terminal (positions + pending orders)."""

from __future__ import annotations

import math
import time
from copy import deepcopy
from typing import Any

# MT5 trade server return codes we mirror in the mock.
RETCODE_DONE = 10009
RETCODE_INVALID_STOPS = 10016


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
                "stops_level": 20,
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
                "stops_level": 25,
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
                "stops_level": 25,
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
                "stops_level": 40,
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
                "stops_level": 5000,
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
                "commission": 0.7,
                "swap": -1.2,
                "profit": 42.0,
                "entry": "out",
                "time": time.time() - 3600,
                "comment": "demo-deal",
            },
            {
                "ticket": 200002,
                "position_id": 200002,
                "symbol": "GBPUSD",
                "side": "sell",
                "volume": 0.10,
                "price": 1.26800,
                "commission": 0.5,
                "swap": -0.8,
                "profit": -15.5,
                "entry": "out",
                "time": time.time() - 7200,
                "comment": "demo-deal",
            },
            {
                "ticket": 200003,
                "position_id": 200003,
                "symbol": "USDJPY",
                "side": "buy",
                "volume": 0.05,
                "price": 149.200,
                "commission": 0.3,
                "swap": 0.5,
                "profit": 28.3,
                "entry": "out",
                "time": time.time() - 10800,
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

    def _pip_value(self, symbol: str, volume: float, price: float) -> float:
        if symbol == "BTCUSD":
            return volume
        if symbol == "XAUUSD":
            return volume * 100
        if symbol == "USDJPY":
            return volume * 1000 / max(price, 1)
        return volume * 100000

    def _profit_at(self, position: dict[str, Any], price: float, volume: float | None = None) -> float:
        """Profit of (part of) a position if it were closed at `price`."""
        vol = float(position["volume"]) if volume is None else float(volume)
        direction = 1 if position["side"] == "buy" else -1
        pip_value = self._pip_value(position["symbol"], vol, price)
        return round(direction * (price - position["price_open"]) * pip_value, 2)

    def _close_price(self, position: dict[str, Any]) -> float:
        q = self._symbols[position["symbol"]]
        return q["bid"] if position["side"] == "buy" else q["ask"]

    def _reprice(self) -> None:
        for p in self._positions.values():
            price = self._close_price(p)
            p["profit"] = self._profit_at(p, price)
            p["price_current"] = price

    def _apply_stops(self) -> list[dict[str, Any]]:
        """Close positions whose SL or TP is touched by the current quote.

        A stop fills at its own price, not at the market price, which is what makes
        the booked profit deterministic. If a gap crosses both levels in one move the
        stop loss wins — the pessimistic side, same as a real broker.
        """
        triggered: list[tuple[int, str, float]] = []
        for ticket, p in self._positions.items():
            price = self._close_price(p)
            sl, tp = p.get("sl"), p.get("tp")
            if p["side"] == "buy":
                hit_sl = sl is not None and price <= sl
                hit_tp = tp is not None and price >= tp
            else:
                hit_sl = sl is not None and price >= sl
                hit_tp = tp is not None and price <= tp
            if hit_sl:
                triggered.append((ticket, "sl", float(sl)))
            elif hit_tp:
                triggered.append((ticket, "tp", float(tp)))
        deals = []
        for ticket, reason, price in triggered:
            deals.append(self._book_close(self._positions[ticket], None, price, reason))
        return deals

    def _mark_to_market(self) -> None:
        self._reprice()
        if self._apply_stops():
            self._reprice()
        self._recalc()

    def _book_close(
        self,
        position: dict[str, Any],
        volume: float | None,
        price: float,
        reason: str,
    ) -> dict[str, Any]:
        """Close (part of) a position at `price`, book the deal and update balance."""
        close_vol = float(position["volume"]) if volume is None else float(volume)
        profit = self._profit_at(position, price, close_vol)
        self._balance = round(self._balance + profit, 2)
        deal = {
            "ticket": self._next_ticket(),
            "position_id": position["ticket"],
            "symbol": position["symbol"],
            "side": "sell" if position["side"] == "buy" else "buy",
            "volume": close_vol,
            "price": price,
            "profit": profit,
            "entry": "out",
            "reason": reason,
            "time": time.time(),
            "comment": position.get("comment", ""),
        }
        self._deals.insert(0, deal)
        if abs(close_vol - float(position["volume"])) < 1e-9:
            del self._positions[int(position["ticket"])]
        else:
            ratio = close_vol / float(position["volume"])
            position["volume"] = round(float(position["volume"]) - close_vol, 2)
            position["margin"] = round(float(position["margin"]) * (1 - ratio), 2)
        self._recalc()
        return deal

    def _normalise_stops(
        self,
        symbol: str,
        side: str,
        ref_price: float,
        sl: float | None,
        tp: float | None,
        trigger_price: float | None = None,
    ) -> dict[str, Any]:
        """Validate SL/TP against side, reference price and the symbol stops level.

        `ref_price` is the price the position opens at, `trigger_price` the price the
        stops are checked against later (bid for a buy, ask for a sell) — that is the
        one the stops level distance is measured from, like MT5 does.

        Returns {"ok": True, "sl": ..., "tp": ...} with prices rounded to symbol digits,
        or {"ok": False, "retcode": 10016, "error": ...} the caller can return as-is.
        """
        s = self._symbols[symbol]
        digits = int(s["digits"])
        point = float(s["point"])
        min_distance = float(s.get("stops_level", 0)) * point
        check_from = ref_price if trigger_price is None else trigger_price
        out: dict[str, Any] = {"ok": True, "sl": None, "tp": None}
        for label, raw in (("sl", sl), ("tp", tp)):
            if raw is None:
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                return self._invalid_stops(f"{label} must be a number, got {raw!r}")
            if not math.isfinite(value) or value <= 0:
                return self._invalid_stops(f"{label} must be a positive finite price, got {raw!r}")
            value = round(value, digits)
            if label == "sl":
                wrong_side = value >= ref_price if side == "buy" else value <= ref_price
                expected = "below" if side == "buy" else "above"
            else:
                wrong_side = value <= ref_price if side == "buy" else value >= ref_price
                expected = "above" if side == "buy" else "below"
            if wrong_side:
                return self._invalid_stops(
                    f"{label} {value} must be {expected} the {side} price {ref_price}"
                )
            if abs(value - check_from) < min_distance - 1e-12:
                return self._invalid_stops(
                    f"{label} {value} is closer than the {symbol} stops level "
                    f"({s.get('stops_level', 0)} points = {round(min_distance, digits)}) "
                    f"from price {check_from}"
                )
            out[label] = value
        return out

    @staticmethod
    def _invalid_stops(message: str) -> dict[str, Any]:
        return {"ok": False, "retcode": RETCODE_INVALID_STOPS, "error": message}

    def set_quote(self, symbol: str, bid: float, ask: float | None = None) -> dict[str, Any]:
        """Move the mock market (mock only) — lets stops be exercised without a terminal."""
        sym = symbol.upper()
        s = self._symbols.get(sym)
        if not s:
            return {"ok": False, "error": f"unknown symbol {symbol}"}
        try:
            new_bid = float(bid)
            new_ask = float(ask) if ask is not None else new_bid + s["point"] * s["spread"]
        except (TypeError, ValueError):
            return {"ok": False, "error": "bid/ask must be numbers"}
        if not (math.isfinite(new_bid) and math.isfinite(new_ask)) or new_bid <= 0 or new_ask <= 0:
            return {"ok": False, "error": "bid/ask must be positive finite prices"}
        if new_ask < new_bid:
            return {"ok": False, "error": "ask must be >= bid"}
        digits = int(s["digits"])
        s["bid"] = round(new_bid, digits)
        s["ask"] = round(new_ask, digits)
        s["last"] = round((s["bid"] + s["ask"]) / 2, digits)
        s["spread"] = round((s["ask"] - s["bid"]) / s["point"])
        closed = self._apply_stops()
        self._reprice()
        self._recalc()
        return {
            "ok": True,
            "symbol": sym,
            "bid": s["bid"],
            "ask": s["ask"],
            "spread": s["spread"],
            "closed_by_stops": closed,
        }

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
        if ot == "market":
            open_price = q["ask"] if side_l == "buy" else q["bid"]
            close_side_price = q["bid"] if side_l == "buy" else q["ask"]
            stops = self._normalise_stops(
                sym, side_l, open_price, sl, tp, trigger_price=close_side_price
            )
            if not stops["ok"]:
                return stops
            sl, tp = stops["sl"], stops["tp"]
            ticket = self._next_ticket()
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
            still_open = self._positions.get(ticket)
            return {
                "ok": True,
                "retcode": RETCODE_DONE,
                "ticket": ticket,
                "position": deepcopy(still_open) if still_open else None,
                "closed_by_stops": None if still_open else self._deals[0],
            }
        if price is None:
            return {"ok": False, "error": "pending order requires price"}
        if ot not in {"buy_limit", "sell_limit", "buy_stop", "sell_stop"}:
            return {"ok": False, "error": f"unsupported order_type {order_type}"}
        stops = self._normalise_stops(sym, side_l, float(price), sl, tp)
        if not stops["ok"]:
            return stops
        sl, tp = stops["sl"], stops["tp"]
        ticket = self._next_ticket()
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
        return {"ok": True, "retcode": RETCODE_DONE, "ticket": ticket, "order": deepcopy(order)}

    def position_close(self, ticket: int, volume: float | None = None) -> dict[str, Any]:
        p = self._positions.get(int(ticket))
        if not p:
            return {"ok": False, "error": f"position {ticket} not found"}
        self._mark_to_market()
        p = self._positions.get(int(ticket))
        if not p:
            # A stop was touched while the close was in flight — report the stop deal.
            stop_deal = next(
                (d for d in self._deals if d.get("position_id") == int(ticket)), None
            )
            return {
                "ok": False,
                "error": f"position {ticket} already closed by {stop_deal.get('reason')}"
                if stop_deal and stop_deal.get("reason")
                else f"position {ticket} not found",
                "deal": stop_deal,
            }
        close_vol = float(volume) if volume is not None else float(p["volume"])
        if close_vol <= 0 or close_vol > p["volume"] + 1e-9:
            return {"ok": False, "error": "invalid close volume"}
        deal = self._book_close(p, close_vol, self._close_price(p), "manual")
        return {"ok": True, "deal": deal, "balance": self._balance}

    def order_cancel(self, ticket: int) -> dict[str, Any]:
        o = self._orders.pop(int(ticket), None)
        if not o:
            return {"ok": False, "error": f"pending order {ticket} not found"}
        return {"ok": True, "cancelled": o}

    def history_deals(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return deal history with profit breakdown (commission, swap, profit)."""
        n = max(1, min(int(limit), 100))
        return [deepcopy(d) for d in self._deals[:n]]

    def symbol_spec(self, symbol: str) -> dict[str, Any]:
        """Return trading constraints from mock specs: digits, lot_step, contract_size."""
        sym = symbol.upper()
        if sym not in self._symbols:
            return {"ok": False, "error": f"unknown symbol {symbol}"}
        s = self._symbols[sym]
        return {
            "ok": True,
            "symbol": sym,
            "digits": s.get("digits", 5),
            "lot_step": 0.01,
            "contract_size": s.get("trade_contract_size", 100000),
            "point": s.get("point"),
            "stops_level": s.get("stops_level", 0),
        }

    def history_deals_paginated(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """Paginated deal history with summary."""
        total = len(self._deals)
        n = max(1, min(int(limit), 100))
        o = max(0, int(offset))
        page = [deepcopy(d) for d in self._deals[o:o + n]]
        total_profit = sum(d.get("profit", 0) for d in page)
        return {
            "ok": True,
            "total": total,
            "offset": o,
            "limit": n,
            "page_profit": round(total_profit, 2),
            "deals": page,
        }

    def account_equity_curve(self) -> dict[str, Any]:
        """Account metrics with equity curve time series."""
        self._recalc()
        now = time.time()
        if not hasattr(self, '_equity_snapshots'):
            self._equity_snapshots: list[dict[str, Any]] = []
        self._equity_snapshots.append({
            "time": now,
            "balance": self._balance,
            "equity": self._equity,
            "margin": self._margin,
        })
        self._equity_snapshots = self._equity_snapshots[-30:]
        return {
            "ok": True,
            "login": self._login,
            "currency": self._currency,
            "leverage": self._leverage,
            "trade_mode": self._trade_mode,
            "balance": self._balance,
            "equity": self._equity,
            "margin": self._margin,
            "margin_free": round(self._equity - self._margin, 2),
            "positions": len(self._positions),
            "pending_orders": len(self._orders),
            "floating_pnl": round(self._equity - self._balance, 2),
            "equity_curve": deepcopy(self._equity_snapshots),
        }
