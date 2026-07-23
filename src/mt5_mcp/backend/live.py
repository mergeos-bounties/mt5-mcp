"""Optional live bridge to MetaTrader 5 (Python API or EA gateway)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from mt5_mcp.config import bridge_file, bridge_url


class LiveBackend:
    name = "live"

    def doctor(self) -> dict[str, Any]:
        url = bridge_url()
        path = bridge_file()
        if url:
            try:
                req = Request(url.rstrip("/") + "/health", method="GET")
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
        # Optional MetaTrader5 package probe
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

    def set_quote(self, symbol: str, bid: float, ask: float | None = None) -> dict[str, Any]:
        return {"ok": False, "error": "set_quote is mock-only — live prices come from the terminal"}

    def _unavailable(self, op: str) -> dict[str, Any]:
        d = self.doctor()
        if d.get("connected"):
            return {
                "ok": False,
                "error": f"live {op} not fully wired for this environment yet",
                "doctor": d,
            }
        return {"ok": False, "error": "live backend not connected", "doctor": d}

    def account(self) -> dict[str, Any]:
        return self._unavailable("account")

    def symbols(self) -> list[dict[str, Any]]:
        return []

    def quote(self, symbol: str) -> dict[str, Any]:
        return self._unavailable("quote")

    def positions(self) -> list[dict[str, Any]]:
        return []

    def orders(self) -> list[dict[str, Any]]:
        return []

    def order_send(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._unavailable("order_send")

    def position_close(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._unavailable("position_close")

    def order_cancel(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._unavailable("order_cancel")

    def history_deals(self, limit: int = 20) -> list[dict[str, Any]]:
        return []

    def history_deals_paginated(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._unavailable("history_deals_paginated")

    def symbol_spec(self, symbol: str) -> dict[str, Any]:
        """Return trading constraints for a symbol (digits, lot step, contract size)."""
        return self._unavailable("symbol_spec")

    def account_equity_curve(self) -> dict[str, Any]:
        return self._unavailable("account_equity_curve")
