# mt5-mcp Live Bridge Design

## Overview

The live bridge enables optional connectivity to a real MetaTrader 5 terminal while keeping the mock backend as the default, zero-dependency mode. This design ensures safety, testability, and zero-friction onboarding.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        mt5-mcp CLI / MCP Server                 │
├─────────────────────────────────────────────────────────────────┤
│  get_backend() ──────────────────────────────────────────────┐  │
│                                                             │   │
│  ┌─────────────────┐         ┌──────────────────────────┐  │   │
│  │  MockBackend    │         │     LiveBackend          │  │   │
│  │  (default)      │         │  (MT5_MCP_MODE=live)     │  │   │
│  │                 │         │                          │  │   │
│  │ • In-memory     │         │  ┌────────────────────┐  │  │   │
│  │ • Seeded demo   │         │  │ Bridge Priority:     │  │   │
│  │ • 5 symbols     │         │  │ 1. MT5_MCP_BRIDGE_  │  │   │
│  │ • Full trading  │         │  │    URL (HTTP)        │  │   │
│  │ • No deps       │         │  │ 2. MT5_MCP_BRIDGE_  │  │   │
│  │                 │         │  │    FILE (JSON RPC)   │  │   │
│  └─────────────────┘         │  │ 3. MetaTrader5 pkg   │  │   │
│                              │  └────────────────────┘  │   │
│                              └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MT5_MCP_MODE` | `mock` | `mock` or `live` |
| `MT5_MCP_BRIDGE_URL` | — | HTTP bridge base URL (e.g., `http://localhost:8080`) |
| `MT5_MCP_BRIDGE_FILE` | — | JSON-RPC request/response file path |
| `MT5_MCP_MAGIC` | `202401` | Magic number for live orders |
| `MT5_MCP_MAX_VOLUME` | `10.0` | Maximum order volume (lots) |
| `MT5_MCP_SYMBOL_ALLOWLIST` | — | Comma-separated allowlisted symbols |

**Key principle**: Mock is default. Live requires explicit opt-in via `MT5_MCP_MODE=live`.

---

## Live Backend Bridge Priority

The `LiveBackend` attempts connections in this order:

1. **HTTP Bridge** (`MT5_MCP_BRIDGE_URL`)
   - `GET /health` for connectivity check
   - JSON-RPC over HTTP for operations
   - 2-second timeout, fails fast

2. **File Bridge** (`MT5_MCP_BRIDGE_FILE`)
   - JSON request/response file polling
   - Useful for local EA-to-Python communication

3. **MetaTrader5 Python Package**
   - Direct `import MetaTrader5` with `mt5.initialize()`
   - Requires MT5 terminal installed and running

**Fails closed**: If no bridge works, all operations return structured errors with `doctor()` diagnostics.

---

## Safety Notes

### 1. Default Mock Mode
```python
# Default behavior requires NO external dependencies
MT5_MCP_MODE=mock  # or unset
mt5-mcp demo        # works everywhere, zero deps
```

### 2. Explicit Live Opt-In
```bash
# Must explicitly enable
export MT5_MCP_MODE=live
export MT5_MCP_BRIDGE_URL=http://localhost:8080
# or
export MT5_MCP_BRIDGE_FILE=/tmp/mt5_bridge.json
```

### 3. Volume & Symbol Guards
```bash
# Cap position size
export MT5_MCP_MAX_VOLUME=1.0

# Restrict tradeable instruments
export MT5_MCP_SYMBOL_ALLOWLIST=EURUSD,GBPUSD
```

### 4. No Secrets in Code
- `.env` files are gitignored
- Credentials passed via environment only
- Magic number isolates our orders

### 5. Fails Closed Design
```python
# LiveBackend._unavailable() returns structured error
{
    "ok": False,
    "error": "live backend not connected",
    "doctor": { "connected": False, "error": "..." }
}
```
All live operations return this instead of crashing or silently failing.

### 6. Mock Data Isolation
- Mock backend uses in-memory state only
- `seed_demo()` is mock-only (`live.seed_demo()` returns error)
- Live mode never touches mock data structures

### 7. Magic Number Isolation
```bash
MT5_MCP_MAGIC=202401  # Only our orders have this magic
```
Prevents interference with manual/manual-EA trades.

---

## Stub Implementation

The `LiveBackend` class in `src/mt5_mcp/backend/live.py` provides:

| Method | Status | Notes |
|--------|--------|-------|
| `doctor()` | ✅ Full | Bridge health + fallback chain |
| `seed_demo()` | ⚠️ Mock-only | Returns error in live |
| `account()` | 🔧 Stub | Returns `_unavailable()` if no bridge |
| `symbols()` | 🔧 Stub | |
| `quote()` | 🔧 Stub | |
| `positions()` | 🔧 Stub | |
| `orders()` | 🔧 Stub | |
| `order_send()` | 🔧 Stub | |
| `position_close()` | 🔧 Stub | |
| `order_cancel()` | 🔧 Stub | |
| `history_deals()` | 🔧 Stub | |
| `symbol_spec()` | 🔧 Stub | Returns bridge info if connected |
| `account_equity_curve()` | 🔧 Stub | |

**Stub pattern**: All methods call `self._unavailable(op)` which runs `doctor()` first. If connected, returns "not fully wired" error; if not connected, returns "bridge not connected" with full diagnostics.

---

## Extending the Live Bridge

To add a real MetaTrader5 integration:

1. **HTTP Bridge** (recommended for remote):
   ```python
   # EA side: HTTP server receiving JSON-RPC
   # Python side: requests.post(bridge_url, json={...})
   ```

2. **File Bridge** (local EA):
   ```python
   # EA writes request.json, Python reads, writes response.json
   # Poll interval: ~100ms
   ```

3. **Direct MetaTrader5 Package**:
   ```python
   import MetaTrader5 as mt5
   mt5.initialize()
   # Use mt5.account_info(), mt5.positions_get(), etc.
   ```

---

## Testing Strategy

| Mode | Tests | Command |
|------|-------|---------|
| Mock | Full suite (24 tests) | `pytest -q` |
| Live (no bridge) | Doctor + error paths | `MT5_MCP_MODE=live pytest -q -k "not mock"` |
| Live (with bridge) | Integration | Requires MT5 terminal |

Mock tests run in CI. Live tests require manual setup.

---

## Future Work

- [ ] Full MetaTrader5 package implementation in `LiveBackend`
- [ ] WebSocket bridge for real-time quotes
- [ ] Async order execution with callbacks
- [ ] Bridge protocol specification (OpenAPI/JSON-RPC)