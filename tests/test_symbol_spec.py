"""Tests for symbol_spec tool."""

from mt5_mcp.backend import mock_instance, set_mode


def test_symbol_spec():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    
    # Test EURUSD
    result = bk.symbol_spec("EURUSD")
    assert result["ok"] is True
    assert result["symbol"] == "EURUSD"
    assert result["digits"] == 5
    assert result["lot_step"] == 0.01
    assert result["contract_size"] == 100000
    
    # Test GBPUSD
    result = bk.symbol_spec("GBPUSD")
    assert result["ok"] is True
    assert result["symbol"] == "GBPUSD"
    assert result["digits"] == 5
    assert result["lot_step"] == 0.01
    assert result["contract_size"] == 100000
    
    # Test unknown symbol
    result = bk.symbol_spec("UNKNOWN")
    assert result["ok"] is False
    assert "unknown symbol" in result["error"]


def test_symbol_spec_case_insensitive():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    
    # Test lowercase
    result = bk.symbol_spec("eurusd")
    assert result["ok"] is True
    assert result["symbol"] == "EURUSD"
    
    # Test mixed case
    result = bk.symbol_spec("GbpUsd")
    assert result["ok"] is True
    assert result["symbol"] == "GBPUSD"