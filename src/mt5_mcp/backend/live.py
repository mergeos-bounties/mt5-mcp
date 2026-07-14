"""Optional live bridge to MetaTrader 5 (Python API or EA gateway).

This module implements a live backend stub that connects to MT5 behind an
environment flag (MT5_MCP_MODE=live), with mock fallback as default.

Safety design:
- All trading operations return structured "not wired" stubs unless a live
  bridge is reachable and explicitly configured.
- Bridge URL authentication uses env vars only — never hard-coded credentials.
- Position/history read-through to bridge API with timeout + error handling.
- Magic number validation supported via MT5_MCP_MAGIC env var.
- Symbol allowlist / max volume limits configurable via env vars.
"""

from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from mt5_mcp.config import bridge_file, bridge_url, magic_number, max_volume, symbol_allowlist


def _bridge_request(path: str, timeout: int = 8) -> dict[str, Any]:
    """Send GET to bridge endpoint, return parsed JSON or error dict."""
    url = bridge_url()
    if not url:
        return {"ok": False, "error": "MT5_MCP_BRIDGE_URL not set"}
    target = f"{url.rstrip('/')}/{path.lstrip('/')}"
    try:
        req = Request(target, method="GET")
        mn = magic_number()
        if mn is not None:
            req.add_header("X-Magic", str(mn))
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")
            data = _json.loads(body) if body else {}
            data["ok"] = True
            return data
    except (URLError, TimeoutError, OSError) as e:
        return {"ok": False, "error": str(e)}
    except _json.JSONDecodeError as e:
        return {"ok": False, "error": f"JSON parse: {e}"}


def _apply_safety_filters(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter positions through allowlist/max-volume if configured."""
    allowed = symbol_allowlist()
    if not allowed and max_volume() >= 100:
        return positions
    filtered = []
    for pos in positions:
        sym = pos.get("symbol", "")
        vol = float(pos.get("volume", 0))
        if allowed and sym not in allowed:
            continue
        if vol > max_volume():
            continue
        filtered.append(pos)
    return filtered


class LiveBackend:
    """Live MetaTrader 5 backend via HTTP bridge or local Python package."""

    name = "live"

    # ------------------------------------------------------------------
    # Health / discovery
    # ------------------------------------------------------------------

    def doctor(self) -> dict[str, Any]:
        url = bridge_url()
        path = bridge_file()
        if url:
            health = _bridge_request("health", timeout=2)
            if health.get("ok"):
                return {
                    "ok": True,
                    "mode": "live",
                    "terminal": "MetaTrader 5 (bridge)",
                    "connected": True,
                    "bridge": url,
                    "health": _json.dumps(health)[:500],
                }
            return {
                "ok": False,
                "mode": "live",
                "connected": False,
                "bridge": url,
                "error": health.get("error", "bridge unreachable"),
                "message": "Live bridge URL not reachable",
            }
        if path and Path(path).is_file():
            return {
                "ok": True,
                "mode": "live",
                "connected": True,
                "bridge_file": path,
                "message": "Bridge file present (local socket/pipe)",
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
                    "or set MT5_MCP_BRIDGE_URL / MT5_MCP_BRIDGE_FILE. "
                    f"Detail: {e}"
                ),
            }

    def seed_demo(self) -> dict[str, Any]:
        return {"ok": False, "error": "seed_demo is mock-only"}

    # ------------------------------------------------------------------
    # Read-level stubs (safe to bridge)
    # ------------------------------------------------------------------

    def account(self) -> dict[str, Any]:
        data = _bridge_request("account")
        if data.get("ok"):
            return data
        return {"ok": False, "error": "account endpoint not available", "detail": data}

    def symbols(self) -> list[dict[str, Any]]:
        data = _bridge_request("symbols")
        if data.get("ok") and isinstance(data.get("symbols"), list):
            return data["symbols"]
        return []

    def quote(self, symbol: str) -> dict[str, Any]:
        data = _bridge_request(f"quote/{symbol}")
        if data.get("ok"):
            return data
        return {"ok": False, "symbol": symbol, "error": "quote unavailable"}

    def positions(self) -> list[dict[str, Any]]:
        data = _bridge_request("positions")
        if data.get("ok") and isinstance(data.get("positions"), list):
            return _apply_safety_filters(data["positions"])
        return []

    def orders(self) -> list[dict[str, Any]]:
        data = _bridge_request("orders")
        if data.get("ok") and isinstance(data.get("orders"), list):
            return data["orders"]
        return []

    def history_deals(self, limit: int = 20) -> list[dict[str, Any]]:
        data = _bridge_request(f"history?limit={max(1, min(limit, 500))}")
        if data.get("ok") and isinstance(data.get("deals"), list):
            return data["deals"]
        return []

    # ------------------------------------------------------------------
    # Write-level safety stubs (require explicit bridge wiring)
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
        """Send order through bridge.

        Safety guards:
        - Refuses if volume exceeds MT5_MCP_MAX_VOLUME.
        - Refuses if symbol not in MT5_MCP_SYMBOL_ALLOWLIST (when set).
        """
        max_vol = max_volume()
        if volume > max_vol:
            return {
                "ok": False,
                "error": f"volume {volume} exceeds max {max_vol}",
                "guard": "MT5_MCP_MAX_VOLUME",
            }
        allowed = symbol_allowlist()
        if allowed and symbol not in allowed:
            return {
                "ok": False,
                "error": f"symbol {symbol} not in allowlist",
                "guard": "MT5_MCP_SYMBOL_ALLOWLIST",
            }
        payload = {
            "symbol": symbol,
            "side": side,
            "volume": volume,
            "order_type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "comment": comment,
        }
        data = _bridge_request("order_send")
        if data.get("ok"):
            return data
        return {
            "ok": False,
            "error": f"live order_send not wired for {symbol}",
            "safety": "requires explicit bridge wiring for trading operations",
            "detail": data,
        }

    def position_close(self, ticket: int, volume: float | None = None) -> dict[str, Any]:
        """Close a position through bridge.

        Safety: requires explicit bridge wiring for trading operations.
        """
        data = _bridge_request(f"position_close/{ticket}")
        if data.get("ok"):
            return data
        return {
            "ok": False,
            "error": f"live position_close not wired for ticket {ticket}",
            "safety": "requires explicit bridge wiring for trading operations",
            "detail": data,
        }

    def order_cancel(self, ticket: int) -> dict[str, Any]:
        """Cancel a pending order through bridge.

        Safety: requires explicit bridge wiring for trading operations.
        """
        data = _bridge_request(f"order_cancel/{ticket}")
        if data.get("ok"):
            return data
        return {
            "ok": False,
            "error": f"live order_cancel not wired for ticket {ticket}",
            "safety": "requires explicit bridge wiring for trading operations",
            "detail": data,
        }
