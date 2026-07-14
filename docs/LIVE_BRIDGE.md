# Live Bridge — HTTP Contract

## Overview

When `MT5_MCP_MODE=live` and `MT5_MCP_BRIDGE_URL` is set, mt5-mcp delegates
positions/history queries to an external bridge server instead of using the mock backend.

## Endpoints

### GET {bridge}/positions

Returns open positions array.

**Response (200):**
```json
{
  "ok": true,
  "positions": [
    {
      "ticket": 200001,
      "symbol": "EURUSD",
      "type": "buy",
      "volume": 0.1,
      "open_price": 1.0850,
      "current_price": 1.0875,
      "profit": 25.0,
      "swap": -0.15,
      "commission": -1.20
    }
  ]
}
```

### GET {bridge}/history?limit=20

Returns recent deal history.

**Response (200):**
```json
{
  "ok": true,
  "deals": [
    {
      "ticket": 190001,
      "time": "2026-07-13T07:00:00Z",
      "symbol": "EURUSD",
      "type": "buy",
      "volume": 0.05,
      "price": 1.0820,
      "commission": -0.60,
      "swap": 0.0,
      "profit": 15.30
    }
  ]
}
```

### Error response

```json
{
  "ok": false,
  "error": "Bridge unavailable"
}
```

## Offline behavior

- If bridge URL returns connection error / timeout, tools return `{"ok": false, "error": "live bridge unavailable"}`
- CI and demo always use mock (no bridge needed)
- Bridge is optional — without it live mode returns structured errors

## Safety

- Never commit bridge URLs with embedded credentials
- Use `MT5_MCP_BRIDGE_URL` env var only
- Bridge should validate requests via magic number or API key


## Safety Architecture

### Design Principles

1. **Mock by default** — `mt5-mcp` always starts in mock mode.
2. **Explicit opt-in** — set `MT5_MCP_MODE=live` + `MT5_MCP_BRIDGE_URL`.
3. **Write stubs firewalled** — `order_send`/`position_close`/`order_cancel` return
   structured "not wired" errors until the bridge explicitly handles them.
4. **Volume guard** — `MT5_MCP_MAX_VOLUME` caps single-order volume (default 100).
5. **Symbol allowlist** — `MT5_MCP_SYMBOL_ALLOWLIST` restricts tradable symbols.
6. **Magic number** — `MT5_MCP_MAGIC` passed as `X-Magic` header for bridge auth.
7. **Env-only secrets** — no credentials in code, config, or logs.

### Risk Matrix

| Operation     | Mode  | Risk  | Guard                                    |
|:-------------|:------|:------|:-----------------------------------------|
| `doctor`     | mock  | None  | returns mock info                        |
| `doctor`     | live  | None  | probe-only, no side effects              |
| `positions`  | live  | None  | read-through bridge, safety-filtered     |
| `history`    | live  | None  | read-through bridge                      |
| `order_send` | live  | High  | max-volume + allowlist + requires wiring |
| `order_send` | no-bridge | Blocked | "not wired" error                   |

### Configuration Reference

| Env Var                 | Default | Purpose                            |
|:------------------------|:--------|:-----------------------------------|
| `MT5_MCP_MODE`          | mock    | `mock` or `live`                   |
| `MT5_MCP_BRIDGE_URL`    | —       | HTTP bridge base URL               |
| `MT5_MCP_BRIDGE_FILE`   | —       | Local socket/pipe path             |
| `MT5_MCP_MAGIC`         | —       | Auth header for bridge requests    |
| `MT5_MCP_MAX_VOLUME`    | 100.0   | Max lot size per order             |
| `MT5_MCP_SYMBOL_ALLOWLIST` | —   | Comma-separated allowed symbols    |
