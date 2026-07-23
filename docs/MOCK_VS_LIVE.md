# Mock vs Live MT5 MCP

## Overview

The MT5 MCP server operates in two modes: **mock** (offline) and **live** (real MetaTrader5 connection). This document explains both paths.

## Mock Mode (Default)

Mock mode requires no MetaTrader5 installation. It returns realistic sample data for all tools.

### Prerequisites

- Python 3.10+
- No MetaTrader5 installation needed
- No MT5 account needed

### Usage

```bash
# Set environment
export MT5_MCP_MODE=mock

# Start the MCP server
python -m mt5_mcp

# CLI demo
python -m mt5_mcp demo

# Doctor check
python -m mt5_mcp doctor
```

### What works offline

| Tool | Mock behavior |
| --- | --- |
| `mt5_account` | Returns sample account with $10,000 balance |
| `mt5_symbols` | Returns EURUSD, GBPUSD, USDJPY, XAUUSD |
| `mt5_symbol_spec` | Returns digits, lot step, margin requirements |
| `mt5_positions` | Returns 2-3 sample positions |
| `mt5_market_order` | Simulates order placement, returns ticket |
| `mt5_deal_history` | Returns sample deal history |
| `mt5_mock_set_quote` | Moves the mock bid/ask so stop levels can be exercised |

### Stop loss / take profit in mock mode

`mt5_order_send` validates SL/TP before anything is opened:

* a buy needs `sl < entry < tp`, a sell needs `tp < entry < sl`;
* both must be finite positive prices and are rounded to the symbol `digits`;
* both must sit at least `stops_level` points away from the price the stop is checked
  against (bid for a buy, ask for a sell) — `mt5_symbol_spec` reports that level;
* anything else is rejected with `retcode 10016` (`TRADE_RETCODE_INVALID_STOPS`) and no
  position or pending order is created.

Once a position is open, every quote refresh checks its stops. A touched level closes the
position **at the stop price**, books the deal with `"reason": "sl"` or `"tp"` and moves the
balance. If one move gaps through both levels the stop loss fills — the pessimistic side,
which is what a real server does.

The mock account lives inside one process, so drive this from a single MCP session (or one
Python snippet) rather than three separate `mt5-mcp call` invocations:

```python
from mt5_mcp.backend import mock_instance

b = mock_instance()
b.order_send("EURUSD", "buy", 1.0, "market", sl=1.08, tp=1.09)
b.set_quote("EURUSD", 1.0795, 1.0797)   # gap through the stop loss
b.history_deals(1)                       # reason: "sl", price 1.08, profit booked
```

## Live Mode

Live mode connects to a real MetaTrader5 terminal via the `MetaTrader5` Python package.

### Prerequisites

1. **MetaTrader5 terminal** installed on Windows
2. **MT5 account** (demo or real)
3. **Python package**: `pip install MetaTrader5`
4. Terminal running and logged in

### Configuration

```bash
# Set environment variables
export MT5_MCP_MODE=live
export MT5_ACCOUNT=12345678
export MT5_PASSWORD=your_password
export MT5_SERVER=MetaQuotes-Demo
export MT5_PATH="C:/Program Files/MetaTrader 5/terminal64.exe"
```

### Safety

- Live mode requires explicit `MT5_MCP_MODE=live` — defaults to mock
- Market orders are real trades in live mode
- All orders include SL/TP validation
- Volume limits enforced per symbol spec

### Switching Modes

```bash
# Runtime mode switch via CLI
python -m mt5_mcp mode --set mock
python -m mt5_mcp mode --set live
```

## CI/Testing

All CI tests run in mock mode. No live connection is needed for development or testing.

```bash
# Run all tests (mock mode)
pytest tests/

# Run specific test
pytest tests/test_symbol_spec.py -v
```

## Troubleshooting

| Problem | Solution |
| --- | --- |
| `MetaTrader5 import error` | Install: `pip install MetaTrader5` (Windows only) |
| `Terminal not found` | Set `MT5_PATH` to terminal64.exe location |
| `Invalid account` | Check account number, password, and server name |
| `Connection failed` | Ensure terminal is running and logged in |
