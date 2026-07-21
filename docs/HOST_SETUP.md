# mt5-mcp — MCP Host Setup

## Cursor

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

1. Open Cursor → Settings → MCP
2. Paste the JSON config
3. Save — Cursor starts mt5-mcp automatically

## Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop.

## Grok (xAI)

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

Add to your Grok custom model config.

## Mock vs live

Start every host in mock mode:

```bash
MT5_MCP_MODE=mock mt5-mcp doctor
MT5_MCP_MODE=mock mt5-mcp demo
```

Mock mode is offline and does not need MetaTrader 5, broker credentials, a simulator, or a bridge.
It is the right mode for first-run checks, CI, and demos.

Live mode is opt-in. Before setting `MT5_MCP_MODE=live`, prepare one of these:

- `MT5_MCP_BRIDGE_URL`, with an HTTP bridge that answers `/health`.
- `MT5_MCP_BRIDGE_FILE`, with a local bridge file path.
- The optional `MetaTrader5` Python package, plus a running and logged-in MetaTrader 5 terminal.

Then check the live connection explicitly:

```bash
MT5_MCP_MODE=live MT5_MCP_BRIDGE_URL=http://127.0.0.1:8765 mt5-mcp doctor
```

If the bridge or terminal is missing, live mode reports `connected: false`; live tools fail closed
or return empty stub data. `mt5-mcp demo` always runs in mock mode and is not proof of live broker
readiness.

## Safety

- Always start with `MT5_MCP_MODE=mock` to verify connectivity
- Switch to `live` only after confirming the bridge is ready
- Never commit `.env` files with real credentials
