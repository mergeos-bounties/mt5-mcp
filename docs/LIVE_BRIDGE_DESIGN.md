# Live MetaTrader5 Python Package Bridge — Design & Safety Notes

## 1. Architecture

```
┌─────────────┐      MCP stdio        ┌────────────────────┐
│ AI Agent    │ ────────────────────▶ │  mt5-mcp server    │
│ (Claude/    │                        │  (FastMCP)        │
│  Cursor/    │                        │                    │
│  Grok)      │                        └────┬───────────┬───┘
└─────────────┘                             │           │
                                            │           │
                                    ┌───────▼──┐  ┌─────▼──────┐
                                    │ Mock     │  │ Live       │
                                    │ Backend  │  │ Backend    │
                                    │ (always  │  │ (optional) │
                                    │ works)   │  │            │
                                    └──────────┘  └─────┬──────┘
                                                        │
                                                    ┌───▼──────────┐
                                                    │ MetaTrader5  │
                                                    │ Python pkg   │
                                                    │ (Windows)    │
                                                    └──────────────┘
```

## 2. Mode Selection

| Env Var | Default | Meaning |
| --- | --- | --- |
| `MT5_MCP_MODE` | `mock` | `mock` or `live` |

- **Mock mode** is the default and **always works** offline
- **Live mode** activates only when `MT5_MCP_MODE=live` AND a bridge is reachable
- Switching at runtime: `mt5-mcp mode --set live`

## 3. Live Backend Stages

### Stage 1: Optional MetaTrader5 Python package probe (current)

The live backend attempts `import MetaTrader5` and `mt5.initialize()`.
If available, it returns terminal info. If not, it returns a structured error.

```python
import MetaTrader5 as mt5
ok = mt5.initialize()
if ok:
    info = mt5.terminal_info()
    mt5.shutdown()
```

### Stage 2: HTTP bridge (PR #26)

When `MT5_MCP_BRIDGE_URL` is set, the live backend forwards read-level
queries (account, symbols, positions, history) to a lightweight HTTP
bridge server that runs alongside the MT5 terminal.

### Stage 3: Full live execution (future)

Write-level operations (order_send, position_close) will route through
the bridge with safety guards enforced server-side.

## 4. Safety Guards

| Guard | Env Var | Default | Effect |
| --- | --- | --- | --- |
| Magic number | `MT5_MCP_MAGIC` | None | Orders tagged with magic; mismatches rejected |
| Max volume | `MT5_MCP_MAX_VOLUME` | 100.0 | Single order volume cap |
| Symbol allowlist | `MT5_MCP_SYMBOL_ALLOWLIST` | None | Only allowlisted symbols can be traded |

**Fails-closed principle**: if the live backend cannot connect, all tools
return structured `{"ok": false, "error": "live backend not connected"}` —
they never silently fall through to mock or execute real trades.

## 5. Testing Strategy

- **All existing CI tests** run in mock mode (no live connection needed)
- **Live-specific tests** use a fixture that mocks the HTTP bridge response
- **Integration tests** (manual): run `MT5_MCP_MODE=live` with a real
  bridge configured and verify doctor/quote/positions return live data

## 6. CI & Demo Behavior

- **CI** always runs `MT5_MCP_MODE=mock`
- **`mt5-mcp demo`** forces mock mode
- **Bridge is optional**: without a working bridge, live mode returns
  structured errors; demos stay on mock

## 7. Implementation Checklist

- [x] `backend/live.py` — optional MT5 package probe
- [x] `backend/live.py` — HTTP bridge URL/file paths
- [x] `config.py` — `MT5_MCP_MAGIC`, `MT5_MCP_MAX_VOLUME`, `MT5_MCP_SYMBOL_ALLOWLIST`
- [x] `safety.py` — magic number, max volume, symbol allowlist guards
- [x] `docs/LIVE_BRIDGE.md` — HTTP bridge contract
- [x] `docs/MOCK_VS_LIVE.md` — mode comparison
- [x] `test_safety.py` — safety guard unit tests
- [ ] Full write-level bridge (order_send, position_close via HTTP)
- [ ] Live mode integration test suite

## 8. Design Decisions

1. **Python package first**: `MetaTrader5` Python package is the canonical
   integration path (Windows only). The HTTP bridge is an alternative for
   headless or cross-platform deployments.

2. **Read-only live first**: Initial live implementation only exposes read
   operations (account, symbols, quotes, positions, history). Write
   operations require additional safety review.

3. **No mock fallback in live mode**: When `MT5_MCP_MODE=live`, if the
   bridge fails, tools return errors — they do not silently use mock data.
   This prevents accidental real-money trades based on stale/mock data.

4. **Magic number enforcement**: Every live order includes the configured
   magic number so MT5's own history can distinguish mt5-mcp orders from
   manual trades.
