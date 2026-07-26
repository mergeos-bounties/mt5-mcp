# Live MetaTrader 5 Bridge Design & Safety Specification

This document details the live execution architecture and safety invariants for `mt5-mcp`.

---

## 1. Overview & Architecture

`LiveBackend` provides an optional, safe bridge to a live or demo MetaTrader 5 terminal or REST gateway.

```
                    ┌─────────────────────────┐
                    │     FastMCP Server      │
                    └────────────┬────────────┘
                                 │
                     ┌───────────┴───────────┐
                     │ get_backend() switch  │
                     └─────┬───────────┬─────┘
                           │           │
                 ┌─────────▼──┐     ┌──▼──────────┐
                 │MockBackend │     │LiveBackend  │
                 └────────────┘     └──────┬──────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         │                                   │
               ┌─────────▼──────────┐              ┌─────────▼──────────┐
               │ MetaTrader5 Python │              │ REST / HTTP Bridge │
               │   Native Package   │              │   (Gateway Mode)   │
               └────────────────────┘              └────────────────────┘
```

---

## 2. Safety Invariants & Execution Guards

To prevent accidental live order execution on production accounts:

1. **Explicit Opt-in**: Live backend is strictly inactive unless `MT5_MODE=live` environment variable is explicitly set. Default mode is always `mock`.
2. **Demo / Real Account Verification**: Live order calls output clear warnings when connected to a real money account vs demo account.
3. **Mandatory Stop-Loss (SL) Enforcement**: Optional configuration `MT5_MANDATORY_SL=1` forces order submissions without SL to be rejected.
4. **Max Volume Guard**: Orders exceeding `MT5_MAX_VOLUME` (default: 5.0 lots) are automatically blocked.

---

## 3. Configuration & Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MT5_MODE` | Backend mode (`mock` or `live`) | `mock` |
| `MT5_MCP_BRIDGE_URL` | REST gateway endpoint URL | `""` |
| `MT5_MCP_BRIDGE_FILE` | IPC socket or bridge file path | `""` |
| `MT5_MAX_VOLUME` | Max lot size permitted per trade | `5.0` |
