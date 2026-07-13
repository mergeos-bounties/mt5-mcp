# mt5-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-5319E7.svg)](https://modelcontextprotocol.io)

**mt5-mcp** is an [MCP](https://modelcontextprotocol.io) server so AI agents can inspect and trade against a **MetaTrader 5** terminal — account, symbols, quotes, orders/positions, history — with a full **offline mock** for CI and demos.

---

## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| **mock** (default) | Windows / CI / no terminal | Seeded demo account, FX/CFD symbols, orders, history |
| **live** | Host has a bridge configured | Optional file/HTTP bridge (see env vars); fails closed if unavailable |

---

## Highlights

| Capability | Description |
| --- | --- |
| **Offline demo** | `mt5-mcp demo` exercises doctor, quotes, market order, history |
| **MCP stdio serve** | Plug into Cursor / Claude / Grok as an MCP server |
| **One-shot call** | `mt5-mcp call …` without a full MCP host |
| **Safety** | Mock never talks to a real broker; live needs explicit env |

---

## Quick start

```powershell
cd mt5-mcp
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"

mt5-mcp version
mt5-mcp demo
mt5-mcp tools list
pytest -q
```

Mock mode needs **no** MetaTrader install.

---

## CLI reference

| Command | Purpose |
| --- | --- |
| `mt5-mcp version` | Version + mode |
| `mt5-mcp demo` | Offline smoke of core backend APIs |
| `mt5-mcp doctor` | Backend health |
| `mt5-mcp serve` | MCP server over **stdio** |
| `mt5-mcp call …` | One-shot tool call |
| `mt5-mcp tools list` | List MCP tools |

```powershell
mt5-mcp serve
```

---

## MCP tools

| Tool | Purpose |
| --- | --- |
| `mt5_mode` | Get/set mock\|live |
| `mt5_doctor` | Connectivity / account health |
| `mt5_seed_demo` | Reset mock account |
| `mt5_account` | Balance, equity, margin, trade mode |
| `mt5_symbols` | Symbol list |
| `mt5_quote` | Bid/ask / last |
| `mt5_positions` | Open positions |
| `mt5_orders` | Pending orders |
| `mt5_order_send` | Market/pending |
| `mt5_position_close` | Close position by ticket |
| `mt5_history_deals` | Deal history |

---

## MCP host config

```json
{
  "mcpServers": {
    "mt5-mcp": {
      "command": "python",
      "args": ["-m", "mt5_mcp"],
      "env": {
        "MT5_MCP_MODE": "mock"
      }
    }
  }
}
```

Also see `examples/cursor_mcp.json`.

---

## Live bridge (optional)

Set env (never commit secrets):

| Variable | Meaning |
| --- | --- |
| `MT5_MCP_MODE` | `mock` or `live` |
| `MT5_MCP_MAGIC` | Optional magic number for live orders | `202401` |
| `MT5_MCP_MAX_VOLUME` | Max order volume cap | `10.0` |
| `MT5_MCP_SYMBOL_ALLOWLIST` | Comma-sep allowlisted symbols | `EURUSD,GBPUSD` |
| `MT5_MCP_BRIDGE_URL` | Optional HTTP bridge base URL |
| `MT5_MCP_BRIDGE_FILE` | Optional request/response JSON file path |

Without a working bridge, **live** mode returns structured errors; demos stay on **mock**.

---

## Development

```powershell
pip install -e ".[dev]"
ruff check src tests
pytest -q
mt5-mcp demo
```

---

## License

[MIT](LICENSE)
