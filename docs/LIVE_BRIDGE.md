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
