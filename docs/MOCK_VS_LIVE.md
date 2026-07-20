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
