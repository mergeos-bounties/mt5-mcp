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

## Safety

- Always start with `MT5_MCP_MODE=mock` to verify connectivity
- Switch to `live` only after confirming the bridge is ready
- Never commit `.env` files with real credentials
