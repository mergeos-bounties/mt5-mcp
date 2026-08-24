"""Comprehensive tests for mt5_symbol_spec — closes issue #23."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "src")

from mt5_mcp.backend.mock import MockBackend


@pytest.fixture()
def backend():
    return MockBackend()


class TestSymbolSpec:
    """Issue #23: symbol spec tool (digits, lot step)."""

    def test_returns_ok(self, backend):
        result = backend.symbol_spec("EURUSD")
        assert result["ok"] is True
        assert result["symbol"] == "EURUSD"

    def test_digits_eurusd(self, backend):
        assert backend.symbol_spec("EURUSD")["digits"] == 5

    def test_digits_usdjpy(self, backend):
        assert backend.symbol_spec("USDJPY")["digits"] == 3

    def test_digits_xauusd(self, backend):
        assert backend.symbol_spec("XAUUSD")["digits"] == 2

    def test_lot_step_is_consistent(self, backend):
        for sym in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]:
            r = backend.symbol_spec(sym)
            assert r["lot_step"] == 0.01, f"{sym} lot_step mismatch"

    def test_contract_size_fx(self, backend):
        for sym in ["EURUSD", "GBPUSD"]:
            r = backend.symbol_spec(sym)
            assert r["contract_size"] == 100000

    def test_contract_size_gold(self, backend):
        assert backend.symbol_spec("XAUUSD")["contract_size"] == 100

    def test_contract_size_btc(self, backend):
        assert backend.symbol_spec("BTCUSD")["contract_size"] == 1

    def test_case_insensitive(self, backend):
        r1 = backend.symbol_spec("eurusd")
        r2 = backend.symbol_spec("EURUSD")
        assert r1 == r2

    def test_unknown_symbol(self, backend):
        result = backend.symbol_spec("INVALID")
        assert result["ok"] is False
        assert "unknown" in result.get("error", "")

    def test_schema_completeness(self, backend):
        required_keys = {"ok", "symbol", "digits", "lot_step", "contract_size"}
        for sym in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]:
            result = backend.symbol_spec(sym)
            missing = required_keys - set(result.keys())
            assert not missing, f"{sym} missing keys: {missing}"
