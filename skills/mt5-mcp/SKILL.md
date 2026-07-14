---
name: mt5-mcp
description: >
  MetaTrader 5 positions/history (mock + live bridge). CLI `mt5-mcp` + MCP stdio serve. Use when the user mentions
  mt5-mcp, /mt5-mcp, or related domain work. One-command Grok install from GitHub.
metadata:
  short-description: "MetaTrader 5 positions/history (mock + live bridge)."
---

# mt5-mcp

## One-command install (Grok)

```bash
pip install "git+https://github.com/mergeos-bounties/mt5-mcp.git" && grok plugin install mergeos-bounties/mt5-mcp --trust
```

Or plugin first, then package:

```bash
grok plugin install mergeos-bounties/mt5-mcp --trust
pip install "git+https://github.com/mergeos-bounties/mt5-mcp.git"
```

Verify:

```bash
mt5-mcp version
mt5-mcp doctor
mt5-mcp demo
mt5-mcp serve   # MCP stdio for hosts
```

## Modes

| Env | Values |
| --- | --- |
| `MT5_MCP_MODE` | `mock` (default) · `live` |

## MCP

```bash
mt5-mcp serve
```

Config ships in plugin `.mcp.json`. Manual: see repo `examples/`.
