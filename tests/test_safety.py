"""Tests for live safety guards."""

import os


def test_max_volume_rejected():
    os.environ["MT5_MCP_MAX_VOLUME"] = "1.0"
    from mt5_mcp.config import max_volume
    assert max_volume() == 1.0


def test_symbol_allowlist():
    os.environ["MT5_MCP_SYMBOL_ALLOWLIST"] = "EURUSD,GBPUSD"
    from mt5_mcp.config import symbol_allowlist
    assert symbol_allowlist() == ["EURUSD", "GBPUSD"]


def test_magic_number():
    os.environ["MT5_MCP_MAGIC"] = "202401"
    from mt5_mcp.config import magic_number
    assert magic_number() == 202401
