"""Tests for symbol_spec tool (digits, lot_step, contract_size)."""

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


def test_symbol_spec_commodities_and_cryptos():
    """Symbol spec should return correct contract sizes for XAUUSD and BTCUSD."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    # XAUUSD (gold) has contract_size 100 and digits 2
    result = bk.symbol_spec("XAUUSD")
    assert result["ok"] is True
    assert result["symbol"] == "XAUUSD"
    assert result["digits"] == 2
    assert result["lot_step"] == 0.01
    assert result["contract_size"] == 100

    # BTCUSD has contract_size 1 (per BTC) and digits 2
    result = bk.symbol_spec("BTCUSD")
    assert result["ok"] is True
    assert result["symbol"] == "BTCUSD"
    assert result["digits"] == 2
    assert result["lot_step"] == 0.01
    assert result["contract_size"] == 1


def test_symbol_spec_usdjpy_jpy_digits():
    """USDJPY should report 3 digits (pipette precision)."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.symbol_spec("USDJPY")
    assert result["ok"] is True
    assert result["symbol"] == "USDJPY"
    assert result["digits"] == 3
    assert result["contract_size"] == 100000


def test_symbol_spec_returns_all_required_fields():
    """Verify every required field is present in the response."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    required_fields = {"ok", "symbol", "digits", "lot_step", "contract_size"}
    result = bk.symbol_spec("EURUSD")
    assert result["ok"] is True
    assert required_fields.issubset(result.keys())