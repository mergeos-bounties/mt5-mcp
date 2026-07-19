from __future__ import annotations

import json
from typing import Any, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from mt5_mcp import __version__
from mt5_mcp.backend import get_backend, switch_mode
from mt5_mcp.config import get_mode, set_mode

app = typer.Typer(help="mt5-mcp — MCP server for MetaTrader 5", no_args_is_help=True)
tools_app = typer.Typer(help="List / probe tools")
app.add_typer(tools_app, name="tools")
console = Console()

TOOL_NAMES = [
    "mt5_mode",
    "mt5_doctor",
    "mt5_seed_demo",
    "mt5_account",
    "mt5_symbols",
    "mt5_symbol_spec",
    "mt5_quote",
    "mt5_positions",
    "mt5_orders",
    "mt5_order_send",
    "mt5_position_close",
    "mt5_order_cancel",
    "mt5_history_deals",
]


@app.command("version")
def version_cmd() -> None:
    rprint({"version": __version__, "mode": get_mode()})


@app.command("doctor")
def doctor_cmd() -> None:
    b = get_backend()
    info = b.doctor()
    info["mt5_mcp_version"] = __version__
    info["mode"] = get_mode()
    rprint(info)


@app.command("status")
def status_cmd() -> None:
    b = get_backend()
    acct = b.account()
    info = {
        "mode": get_mode(),
        "balance": acct.get("balance", 0),
        "equity": acct.get("equity", 0),
        "positions": acct.get("positions", 0),
        "pending_orders": acct.get("pending_orders", 0),
        "login": acct.get("login"),
        "server": acct.get("server"),
        "currency": acct.get("currency"),
    }
    rprint(info)


@app.command("demo")
def demo_cmd() -> None:
    """Offline smoke: seed mock account and trade a tiny position."""
    set_mode("mock")
    b = get_backend()
    rprint(b.seed_demo())
    rprint(b.doctor())
    rprint({"account": b.account()})
    rprint({"quote": b.quote("EURUSD")})
    sent = b.order_send("EURUSD", "buy", 0.10, "market", sl=1.08, tp=1.09, comment="demo")
    rprint({"order_send": sent})
    rprint({"positions": b.positions()})
    ticket = int(sent["ticket"])
    rprint({"close": b.position_close(ticket)})
    rprint({"deals": b.history_deals(5)})
    pend = b.order_send("GBPUSD", "sell", 0.05, "sell_limit", price=1.2700)
    rprint({"pending": pend})
    if pend.get("ok"):
        rprint({"cancel": b.order_cancel(int(pend["ticket"]))})
    rprint({"account_after": b.account()})
    rprint("mt5-mcp demo complete (mock).")


@tools_app.command("list")
def tools_list() -> None:
    table = Table(title="mt5-mcp tools")
    table.add_column("Tool")
    for n in TOOL_NAMES:
        table.add_row(n)
    console.print(table)


@app.command("symbol_spec")
def symbol_spec_cmd(symbol: str = typer.Argument(..., help="Symbol e.g. EURUSD")) -> None:
    """Return trading constraints for a symbol (digits, lot_step, contract_size)."""
    b = get_backend()
    rprint(b.symbol_spec(symbol))


@app.command("call")
def call_cmd(
    tool: str = typer.Argument(..., help="Short name e.g. account or mt5_account"),
    arg: Optional[list[str]] = typer.Argument(None, help="key=value pairs"),
) -> None:
    b = get_backend()
    name = tool if tool.startswith("mt5_") else f"mt5_{tool}"
    kv: dict[str, Any] = {}
    for a in arg or []:
        if "=" in a:
            k, v = a.split("=", 1)
            try:
                kv[k] = json.loads(v)
            except json.JSONDecodeError:
                kv[k] = v

    dispatch = {
        "mt5_mode": lambda: switch_mode(str(kv.get("mode", get_mode()))),
        "mt5_doctor": b.doctor,
        "mt5_seed_demo": b.seed_demo,
        "mt5_account": b.account,
        "mt5_symbols": b.symbols,
        "mt5_symbol_spec": lambda: b.symbol_spec(str(kv.get("symbol", "EURUSD"))),
        "mt5_quote": lambda: b.quote(str(kv.get("symbol", "EURUSD"))),
        "mt5_positions": b.positions,
        "mt5_orders": b.orders,
        "mt5_order_send": lambda: b.order_send(
            str(kv.get("symbol", "EURUSD")),
            str(kv.get("side", "buy")),
            float(kv.get("volume", 0.1)),
            str(kv.get("order_type", "market")),
            kv.get("price"),
            kv.get("sl"),
            kv.get("tp"),
            str(kv.get("comment", "")),
        ),
        "mt5_position_close": lambda: b.position_close(
            int(kv.get("ticket", 0)),
            float(kv["volume"]) if "volume" in kv else None,
        ),
        "mt5_order_cancel": lambda: b.order_cancel(int(kv.get("ticket", 0))),
        "mt5_history_deals": lambda: b.history_deals(int(kv.get("limit", 20))),
    }
    if name not in dispatch:
        raise typer.BadParameter(f"unknown tool {name}")
    rprint(dispatch[name]())


@app.command("serve")
def serve_cmd() -> None:
    from mt5_mcp.server import run_stdio

    run_stdio()


def main() -> None:
    app()


if __name__ == "__main__":
    app()
