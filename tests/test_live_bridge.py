"""Tests for the live MetaTrader5 bridge (mock-free, safety-focused)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "src")

from mt5_mcp.backend.live import LiveBackend


@pytest.fixture()
def backend():
    return LiveBackend()


class TestDoctor:
    def test_no_bridge_no_package(self, backend):
        """Without bridge or package, doctor returns not connected."""
        with patch.dict("sys.modules", {"MetaTrader5": None}):
            result = backend.doctor()
        assert result["ok"] is False
        assert result["connected"] is False
        assert "No live bridge" in result.get("message", "")

    def test_bridge_url_health_ok(self, backend):
        """With a reachable bridge URL, doctor reports connected."""
        fake_resp = MagicMock()
        fake_resp.read.return_value = b'{"status": "ok"}'
        fake_resp.__enter__ = MagicMock(return_value=fake_resp)
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("mt5_mcp.backend.live.bridge_url", return_value="http://localhost:8080"):
            with patch("mt5_mcp.backend.live.urlopen", return_value=fake_resp):
                result = backend.doctor()
        assert result["ok"] is True
        assert result["connected"] is True


class TestSafetyValidation:
    def test_volume_must_be_positive(self, backend):
        with pytest.raises(ValueError, match="positive"):
            backend._validate_order(0, sl=1.0, tp=1.1)

    def test_max_volume_cap(self, backend):
        with pytest.raises(ValueError, match="max allowed"):
            backend._validate_order(999999, sl=1.0, tp=1.1)

    def test_sl_is_mandatory(self, backend):
        with pytest.raises(ValueError, match="mandatory"):
            backend._validate_order(0.01, sl=None, tp=1.1)

    def test_valid_order_passes(self, backend):
        backend._validate_order(0.01, sl=0.99, tp=1.10)

    def test_symbol_allowlist_blocked(self, backend):
        with patch("mt5_mcp.backend.live.symbol_allowlist", return_value=["EURUSD"]):
            with pytest.raises(ValueError, match="allowlist"):
                backend._check_symbol("GBPUSD")

    def test_symbol_allowlist_allowed(self, backend):
        with patch("mt5_mcp.backend.live.symbol_allowlist", return_value=["EURUSD"]):
            backend._check_symbol("EURUSD")


class TestOrderSend:
    def test_order_send_invalid_side(self, backend):
        mock_mt5 = MagicMock()
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.ORDER_TYPE_SELL = 1
        with patch.object(backend, "_ensure_init", return_value=mock_mt5):
            # SL is mandatory so provide it; side is invalid
            result = backend.order_send("EURUSD", "invalid", 0.01, sl=1.0)
        assert result["ok"] is False
        assert "Invalid side" in result["error"]

    def test_order_send_missing_sl_rejected_before_init(self, backend):
        """Missing SL should raise before any MT5 init happens."""
        with pytest.raises(ValueError, match="mandatory"):
            backend.order_send("EURUSD", "buy", 0.01, sl=None)


class TestAccount:
    def test_account_with_mock_mt5(self, backend):
        mock_mt5 = MagicMock()
        acct = MagicMock()
        acct.login = 12345
        acct.name = "Test"
        acct.balance = 10000.0
        acct.equity = 10500.0
        acct.margin_free = 9000.0
        acct.currency = "USD"
        acct.leverage = 100
        mock_mt5.account_info.return_value = acct
        mock_mt5.terminal_info.return_value = MagicMock()

        with patch.object(backend, "_mt5", return_value=mock_mt5):
            with patch.object(backend, "_ensure_init", return_value=mock_mt5):
                result = backend.account()
        assert result["ok"] is True
        assert result["balance"] == 10000.0

    def test_account_connection_error(self, backend):
        with patch.object(backend, "_ensure_init", side_effect=ConnectionError("no")):
            result = backend.account()
        assert result.get("ok") is False or "error" in str(result)
