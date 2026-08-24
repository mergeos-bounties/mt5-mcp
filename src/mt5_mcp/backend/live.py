"""Optional live bridge to MetaTrader 5 (native package or EA gateway).

Safety-first design:
- Live mode is opt-in via MT5_MCP_MODE=live
- Max volume cap enforced server-side (MT5_MCP_MAX_VOLUME, default 100)
- Symbol allowlist supported (MT5_MCP_SYMBOL_ALLOWLIST)
- Mandatory SL enforcement on every order (reject if missing)
"""

from __future__ import annotations

import json

import logging
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from mt5_mcp.config import bridge_file, bridge_url, max_volume, symbol_allowlist

logger = logging.getLogger(__name__)


class LiveBackend:
    name = "live"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _mt5(self):
        """Import and return the MetaTrader5 package or raise."""
        import MetaTrader5 as mt5  # type: ignore

        return mt5

    def _ensure_init(self) -> Any:
        """Ensure the MetaTrader5 terminal connection is initialized."""
        mt5 = self._mt5()
        info = mt5.terminal_info()
        if info is None:
            if not mt5.initialize():
                raise ConnectionError(
                    f"MetaTrader5 initialize() failed: {mt5.last_error()}"
                )
        return mt5

    def _check_symbol(self, symbol: str) -> None:
        allow = symbol_allowlist()
        if allow and symbol not in allow:
            raise ValueError(f"Symbol {symbol!r} not in allowlist")

    def _validate_order(self, volume: float, sl: float | None, tp: float | None):
        if volume <= 0:
            raise ValueError("Volume must be positive")
        cap = max_volume()
        if volume > cap:
            raise ValueError(f"Volume {volume} exceeds max allowed {cap}")
        if sl is None:
            raise ValueError("Stop-loss (sl) is mandatory for live orders")

    def _bridge_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = bridge_url()
        if not url:
            raise RuntimeError("MT5_MCP_BRIDGE_URL not set")
        req = Request(  # noqa: S310
            url.rstrip("/") + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:  # noqa: S310
            return json.loads(resp.read())

    # ------------------------------------------------------------------
    # Doctor / health
    # ------------------------------------------------------------------

    def doctor(self) -> dict[str, Any]:
        url = bridge_url()
        path = bridge_file()
        if url:
            try:
                req = Request(url.rstrip("/") + "/health", method="GET")  # noqa: S310
                with urlopen(req, timeout=2) as resp:  # noqa: S310
                    body = resp.read().decode("utf-8", errors="replace")
                return {
                    "ok": True,
                    "mode": "live",
                    "terminal": "MetaTrader 5 (bridge)",
                    "connected": True,
                    "bridge": url,
                    "health": body[:500],
                }
            except (URLError, TimeoutError, OSError) as e:
                return {
                    "ok": False,
                    "mode": "live",
                    "connected": False,
                    "bridge": url,
                    "error": str(e),
                    "message": "Live bridge URL not reachable",
                }
        if path and Path(path).is_file():
            return {
                "ok": True,
                "mode": "live",
                "connected": True,
                "bridge_file": path,
                "message": "Bridge file present",
            }
        try:
            import MetaTrader5 as mt5  # type: ignore

            ok = bool(mt5.initialize())
            info = mt5.terminal_info()
            if ok:
                mt5.shutdown()
            return {
                "ok": ok,
                "mode": "live",
                "connected": ok,
                "terminal": "MetaTrader5 package",
                "info": str(info)[:300] if info else None,
            }
        except Exception as e:  # noqa: BLE001 — optional dependency
            return {
                "ok": False,
                "mode": "live",
                "connected": False,
                "message": (
                    "No live bridge. Install MetaTrader5 package + terminal, "
                    f"or set MT5_MCP_BRIDGE_URL / MT5_MCP_BRIDGE_FILE. "
                    f"Detail: {e}"
                ),
            }

    def seed_demo(self) -> dict[str, Any]:
        return {"ok": False, "error": "seed_demo is mock-only"}

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    def _unavailable(self, op: str) -> dict[str, Any]:
        d = self.doctor()
        if d.get("connected"):
            return {
                "ok": False,
                "error": f"live {op} not fully wired for this environment yet",
                "doctor": d,
            }
        return {"ok": False, "error": "live backend not connected", "doctor": d}

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    def account(self) -> dict[str, Any]:
        try:
            mt5 = self._ensure_init()
            acct = mt5.account_info()
            if acct is None:
                return {"ok": False, "error": "account_info() returned None"}
            return {
                "ok": True,
                "login": acct.login,
                "name": acct.name,
                "balance": acct.balance,
                "equity": acct.equity,
                "margin_free": acct.margin_free,
                "currency": acct.currency,
                "leverage": acct.leverage,
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("live account() failed: %s", e)
            return self._unavailable("account")

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def symbols(self) -> list[dict[str, Any]]:
        try:
            mt5 = self._ensure_init()
            raw = mt5.symbols_get()
            if raw is None:
                return []
            allow = symbol_allowlist()
            result = [
                {
                    "symbol": s.name,
                    "description": s.description,
                    "digits": s.digits,
                    "visible": s.visible,
                }
                for s in raw
                if s.visible and (allow is None or s.name in allow)
            ]
            return result[:100]  # cap to avoid huge payloads
        except Exception as e:  # noqa: BLE001
            logger.warning("live symbols() failed: %s", e)
            return []

    def quote(self, symbol: str) -> dict[str, Any]:
        try:
            mt5 = self._ensure_init()
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {"ok": False, "error": f"No tick data for {symbol}"}
            return {
                "ok": True,
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "time": tick.time,
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("live quote(%s) failed: %s", symbol, e)
            return self._unavailable("quote")

    def symbol_spec(self, symbol: str) -> dict[str, Any]:
        try:
            mt5 = self._ensure_init()
            info = mt5.symbol_info(symbol)
            if info is None:
                return {"ok": False, "error": f"No symbol info for {symbol}"}
            return {
                "ok": True,
                "symbol": symbol,
                "digits": info.digits,
                "point": info.point,
                "trade_contract_size": info.trade_contract_size,
                "volume_min": info.volume_min,
                "volume_max": info.volume_max,
                "volume_step": info.volume_step,
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("live symbol_spec(%s) failed: %s", symbol, e)
            return self._unavailable("symbol_spec")

    # ------------------------------------------------------------------
    # Positions & orders
    # ------------------------------------------------------------------

    def positions(self) -> list[dict[str, Any]]:
        try:
            mt5 = self._ensure_init()
            raw = mt5.positions_get()
            if raw is None:
                return []
            return [
                {
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": "buy" if p.type == 0 else "sell",
                    "volume": p.volume,
                    "price_open": p.price_open,
                    "sl": p.sl,
                    "tp": p.tp,
                    "profit": p.profit,
                }
                for p in raw
            ]
        except Exception as e:  # noqa: BLE001
            logger.warning("live positions() failed: %s", e)
            return []

    def orders(self) -> list[dict[str, Any]]:
        try:
            mt5 = self._ensure_init()
            raw = mt5.orders_get()
            if raw is None:
                return []
            return [
                {
                    "ticket": o.ticket,
                    "symbol": o.symbol,
                    "type": o.type,
                    "volume": o.volume_current,
                    "price_open": o.price_open,
                }
                for o in raw
            ]
        except Exception as e:  # noqa: BLE001
            logger.warning("live orders() failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # Trading (safety-guarded)
    # ------------------------------------------------------------------

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
        self._check_symbol(symbol)
        self._validate_order(volume, sl, tp)

        try:
            mt5 = self._ensure_init()

            order_type_map = {"buy": mt5.ORDER_TYPE_BUY, "sell": mt5.ORDER_TYPE_SELL}
            ot = order_type_map.get(side.lower())
            if ot is None:
                return {"ok": False, "error": f"Invalid side: {side}"}

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": ot,
                "sl": sl,
                "tp": tp,
                "comment": comment[:31],  # MT5 limit
                "type_time": mt5.ORDER_TIME_GTC,
            }
            if price:
                request["price"] = price

            result = mt5.order_send(request)
            if result is None:
                return {"ok": False, "error": f"order_send failed: {mt5.last_error()}"}

            return {
                "ok": result.retcode == mt5.TRADE_RETCODE_DONE,
                "retcode": result.retcode,
                "deal": result.deal,
                "order": result.order,
                "volume": result.volume,
                "price": result.price,
                "comment": result.comment,
            }
        except Exception as e:  # noqa: BLE001
            logger.error("live order_send failed: %s", e)
            return {"ok": False, "error": str(e)}

    def position_close(self, ticket: int, volume: float | None = None) -> dict[str, Any]:
        try:
            mt5 = self._ensure_init()
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return {"ok": False, "error": f"Position {ticket} not found"}
            pos = positions[0]

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": pos.symbol,
                "volume": volume or pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                "comment": f"close #{ticket}",
            }
            result = mt5.order_send(close_request)
            if result is None:
                return {"ok": False, "error": f"close failed: {mt5.last_error()}"}
            return {
                "ok": result.retcode == mt5.TRADE_RETCODE_DONE,
                "retcode": result.retcode,
                "ticket": ticket,
            }
        except Exception as e:  # noqa: BLE001
            logger.error("live position_close(%s) failed: %s", ticket, e)
            return {"ok": False, "error": str(e)}

    def order_cancel(self, ticket: int) -> dict[str, Any]:
        try:
            mt5 = self._ensure_init()
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
            }
            result = mt5.order_send(request)
            if result is None:
                return {"ok": False, "error": f"cancel failed: {mt5.last_error()}"}
            return {"ok": result.retcode == mt5.TRADE_RETCODE_DONE, "ticket": ticket}
        except Exception as e:  # noqa: BLE001
            logger.error("live order_cancel(%s) failed: %s", ticket, e)
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def history_deals(self, limit: int = 20) -> list[dict[str, Any]]:
        try:
            mt5 = self._ensure_init()
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)
            start = now - timedelta(days=30)
            raw = mt5.history_deals_get(start, now)
            if raw is None:
                return []
            deals = [
                {
                    "ticket": d.ticket,
                    "order": d.order,
                    "symbol": d.symbol,
                    "type": d.type,
                    "volume": d.volume,
                    "price": d.price,
                    "profit": d.profit,
                    "time": d.time,
                }
                for d in raw
            ]
            return deals[-limit:]
        except Exception as e:  # noqa: BLE001
            logger.warning("live history_deals() failed: %s", e)
            return []

    def history_deals_paginated(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        all_deals = self.history_deals(limit=offset + limit)
        page = all_deals[offset : offset + limit]
        return {"deals": page, "total": len(all_deals), "has_more": len(all_deals) > offset + limit}

    def account_equity_curve(self) -> dict[str, Any]:
        return self._unavailable("account_equity_curve")


