# mt5-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-5319E7.svg)](https://modelcontextprotocol.io)

**mt5-mcp** is an [MCP](https://modelcontextprotocol.io) server so AI agents can inspect and trade against a **MetaTrader 5** terminal — account, symbols, quotes, orders/positions, history — with a full **offline mock** for CI and demos.

---

## Install (one command)

### Grok — recommended

```bash
pip install "git+https://github.com/mergeos-bounties/mt5-mcp.git" && grok plugin install mergeos-bounties/mt5-mcp --trust
```

This installs the **Python CLI** (`mt5-mcp`) and the **Grok plugin** (skill + MCP server from `.mcp.json`).

Check:

```bash
mt5-mcp version
mt5-mcp doctor
mt5-mcp demo
grok plugin list
grok mcp list
```

Local clone:

```bash
git clone https://github.com/mergeos-bounties/mt5-mcp.git
cd mt5-mcp
pip install -e ".[dev]"
grok plugin install . --trust
```

### Other agents (stdio MCP)

After `pip install "git+https://github.com/mergeos-bounties/mt5-mcp.git"`, point any MCP host at:

| Field | Value |
| --- | --- |
| command | `mt5-mcp` |
| args | `["serve"]` |
| env | `MT5_MCP_MODE=mock` |

**Claude Desktop** — merge [examples/claude_desktop_config.json](examples/claude_desktop_config.json) into Claude MCP config.

**Cursor** — merge [examples/cursor_mcp.json](examples/cursor_mcp.json).

**Grok config.toml** (manual, without plugin):

```toml
[mcp_servers.mt5_mcp]
command = "mt5-mcp"
args = ["serve"]
env = { MT5_MCP_MODE = "mock" }
enabled = true
```

**One-liner via Grok CLI:**

```bash
pip install "git+https://github.com/mergeos-bounties/mt5-mcp.git"
grok mcp add mt5-mcp -- mt5-mcp serve
```


## Supported AI agents / hosts

| Host | Support | Install |
| --- | --- | --- |
| **Grok** (CLI / TUI / Build) | **Yes** | `grok plugin install mergeos-bounties/mt5-mcp --trust` then `pip install "git+https://github.com/mergeos-bounties/mt5-mcp.git"` |
| **Claude Desktop** | **Yes** | Copy [examples/claude_desktop_config.json](examples/claude_desktop_config.json) into Claude MCP settings |
| **Cursor** | **Yes** | Merge [examples/cursor_mcp.json](examples/cursor_mcp.json) into Cursor MCP config |
| **Claude Code** | **Yes** | stdio MCP: same `command`/`args` as Claude Desktop / Grok |
| **VS Code** (MCP / Continue / Cline) | **Yes** | Generic stdio server config pointing at `mt5-mcp serve` |
| **Windsurf / Cascade** | **Yes** | stdio MCP entry with `mt5-mcp` + `serve` |
| **Codex CLI** | **Yes** (stdio) | Register MCP server command `mt5-mcp serve` in Codex MCP settings |
| **ChatGPT Desktop** | **Partial** | Only if host supports custom MCP stdio servers |
| **Gemini CLI** | **Partial** | Only if MCP stdio plugins are enabled |

All packages speak **MCP over stdio** (`mt5-mcp serve`). Default mode is **mock** (offline, no simulator, terminal, or bridge required).


---
## Modes

| Mode | When | Behavior |
| --- | --- | --- |
| **mock** (default) | Windows / CI / no terminal | Seeded demo account, FX/CFD symbols, orders, history |
| **live** | Host has a bridge configured | Optional file/HTTP bridge (see env vars); fails closed if unavailable |

---

## Mock vs live setup

Use **mock** mode first. It is the supported offline path for installs, demos, CI, and host
connectivity checks:

```bash
MT5_MCP_MODE=mock mt5-mcp doctor
MT5_MCP_MODE=mock mt5-mcp demo
```

Use **live** mode only on a machine prepared for broker access. A live setup needs at least one
of these prerequisites:

- `MT5_MCP_BRIDGE_URL` pointing to an HTTP bridge with a `/health` endpoint.
- `MT5_MCP_BRIDGE_FILE` pointing to a local request/response bridge file.
- The optional `MetaTrader5` Python package plus a running, logged-in MetaTrader 5 terminal.

If those prerequisites are missing or unreachable, `mt5-mcp doctor` reports `connected: false`
and live tools fail closed or return empty stub data. `mt5-mcp demo` always switches back to mock
mode so it never exercises a live broker connection.

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
| `mt5-mcp status` | Mode, balance, equity, positions, orders |
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
|| `mt5_symbols` | Symbol list |
|| `mt5_symbol_spec` | Symbol trading constraints |
|| `mt5_quote` | Bid/ask / last |
| `mt5_positions` | **Open positions** (filled market orders) |
| `mt5_orders` | **Pending orders** (limit/stop, not yet filled) |
| `mt5_order_send` | Market/pending |
| `mt5_position_close` | Close position by ticket |
| `mt5_history_deals` | Deal history |
| `mt5://account` (resource) | Account + positions snapshot |

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

| Variable | Meaning | Default / example |
| --- | --- | --- |
| `MT5_MCP_MODE` | Backend mode: `mock` or `live` | `mock` |
| `MT5_MCP_MAGIC` | Optional magic number passed to live bridge/order wiring | unset / `202401` |
| `MT5_MCP_MAX_VOLUME` | Max live order volume cap if live order wiring is enabled | `100.0` when unset |
| `MT5_MCP_SYMBOL_ALLOWLIST` | Optional comma-separated symbol allowlist | unset / `EURUSD,GBPUSD` |
| `MT5_MCP_BRIDGE_URL` | Optional HTTP bridge base URL for live mode | unset / `http://127.0.0.1:8765` |
| `MT5_MCP_BRIDGE_FILE` | Optional local request/response JSON bridge file path | unset |

Without a working bridge, **live** mode returns structured errors; demos stay on **mock**.


---

## Safety

| Rule | Detail |
| --- | --- |
| **Mock-only env** | Copy `examples/env.mock.example` → `.env` and keep `MT5_MCP_MODE=mock` |
| **No secrets in git** | Add `.env` to `.gitignore` — never commit live broker credentials |
| **Max volume** | Set `MT5_MCP_MAX_VOLUME` to cap any single order in live mode |
| **Symbol allowlist** | Restrict tradeable symbols via `MT5_MCP_SYMBOL_ALLOWLIST` (comma-sep) |

---

## Deal history


#### Deal history fields

| Field | Type | Description |
| --- | --- | --- |
| `ticket` | int | Deal ID |
| `time` | str | Timestamp |
| `symbol` | str | Instrument |
| `type` | str | Deal type (buy/sell) |
| `volume` | float | Lot size |
| `price` | float | Execution price |
| `commission` | float | Broker commission (mock) |
| `swap` | float | Overnight swap (mock) |
| `profit` | float | Net P&L (mock) |

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
