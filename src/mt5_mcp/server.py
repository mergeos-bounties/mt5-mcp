"""FastMCP server: MetaTrader 5 tools for AI agents."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from mt5_mcp.backend import get_backend, switch_mode
from mt5_mcp.config import get_mode

mcp = FastMCP(
    "mt5-mcp",
    instructions=(
        "MetaTrader 5 MCP server. Prefer mock mode offline. "
        "Typical flow: mt5_doctor → mt5_account → mt5_quote → "
        "mt5_order_send → mt5_positions → mt5_position_close."
    ),
)


def _j(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def mt5_mode(mode: str | None = None) -> str:
    """Get or set MT5 backend mode (mock|live)."""
    if mode:
        return _j(switch_mode(mode))
    b = get_backend()
    return _j({"mode": get_mode(), "backend": b.name, "doctor": b.doctor()})


@mcp.tool()
def mt5_doctor() -> str:
    """Check mock/live connectivity and account health."""
    return _j(get_backend().doctor())


@mcp.tool()
def mt5_seed_demo() -> str:
    """Reset the mock MT5 demo account (mock only)."""
    return _j(get_backend().seed_demo())


@mcp.tool()
def mt5_account() -> str:
    """Account balance, equity, margin, trade mode."""
    return _j(get_backend().account())


@mcp.tool()
def mt5_symbols() -> str:
    """List tradeable symbols."""
    return _j(get_backend().symbols())


@mcp.tool()
def mt5_quote(symbol: str) -> str:
    """Bid/ask/last quote for a symbol."""
    return _j(get_backend().quote(symbol))


@mcp.tool()
def mt5_positions() -> str:
    """List open positions."""
    return _j(get_backend().positions())


@mcp.tool()
def mt5_orders() -> str:
    """List pending orders."""
    return _j(get_backend().orders())


@mcp.tool()
def mt5_order_send(
    symbol: str,
    side: str,
    volume: float,
    order_type: str = "market",
    price: float | None = None,
    sl: float | None = None,
    tp: float | None = None,
    comment: str = "",
) -> str:
    """Open market position or place pending order."""
    return _j(
        get_backend().order_send(symbol, side, volume, order_type, price, sl, tp, comment)
    )


@mcp.tool()
def mt5_position_close(ticket: int, volume: float | None = None) -> str:
    """Close position by ticket (optional partial volume)."""
    return _j(get_backend().position_close(ticket, volume))


@mcp.tool()
def mt5_order_cancel(ticket: int) -> str:
    """Cancel a pending order ticket."""
    return _j(get_backend().order_cancel(ticket))


@mcp.tool()
def mt5_history_deals(limit: int = 20) -> str:
    """Recent deal history."""
    return _j(get_backend().history_deals(limit=limit))


@mcp.tool()
def mt5_history_deals_paginated(limit: int = 20, offset: int = 0) -> str:
    """Paginated deal history with profit summary."""
    return _j(get_backend().history_deals_paginated(limit=limit, offset=offset))


@mcp.tool()
def mt5_symbol_spec(symbol: str) -> str:
    """Return trading constraints for a symbol (digits, lot_step, contract_size)."""
    return _j(get_backend().symbol_spec(symbol))


@mcp.tool()
def mt5_account_equity_curve() -> str:
    """Account metrics with equity curve time series."""
    return _j(get_backend().account_equity_curve())


@mcp.tool()
def mt5_positions_detailed() -> str:
    """Open positions with detailed PnL fields (floating profit, current price, margin)."""
    return _j(get_backend().positions())


def run_stdio() -> None:
    mcp.run(transport="stdio")
