"""Tests for SL/TP validation and trigger logic — closes issue #20."""

from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "src")

from mt5_mcp.backend.mock import MockBackend

# EURUSD mock prices: bid=1.08515, ask=1.08535
EURUSD_BID = 1.08515
EURUSD_ASK = 1.08535


@pytest.fixture()
def backend():
    return MockBackend()


class TestSLTPValidation:
    """Issue #20: place market order with SL/TP (mock)."""

    def test_buy_sl_above_entry_rejected(self, backend):
        """Buy with SL above entry price should be rejected."""
        result = backend.order_send("EURUSD", "buy", 0.01, sl=1.20)
        assert result["ok"] is False
        assert "below entry" in result["error"]

    def test_buy_tp_below_entry_rejected(self, backend):
        result = backend.order_send("EURUSD", "buy", 0.01, tp=0.90)
        assert result["ok"] is False
        assert "above entry" in result["error"]

    def test_sell_sl_below_entry_rejected(self, backend):
        result = backend.order_send("EURUSD", "sell", 0.01, sl=0.90)
        assert result["ok"] is False
        assert "above entry" in result["error"]

    def test_sell_tp_above_entry_rejected(self, backend):
        """Sell TP must be below entry price."""
        result = backend.order_send("EURUSD", "sell", 0.01, tp=1.50)
        assert result["ok"] is False
        assert "below entry" in result["error"]

    def test_buy_with_valid_sl_tp(self, backend):
        """Buy: SL below entry, TP above entry → accepted."""
        result = backend.order_send("EURUSD", "buy", 0.01, sl=1.07, tp=1.10)
        assert result["ok"] is True
        assert result["position"]["sl"] == 1.07
        assert result["position"]["tp"] == 1.10

    def test_sell_with_valid_sl_tp(self, backend):
        """Sell: SL above entry (~1.085), TP below entry → accepted."""
        result = backend.order_send("EURUSD", "sell", 0.01, sl=1.10, tp=1.07)
        assert result["ok"] is True
        assert result["position"]["sl"] == 1.10
        assert result["position"]["tp"] == 1.07

    def test_order_without_sl_tp_still_works(self, backend):
        result = backend.order_send("EURUSD", "buy", 0.01)
        assert result["ok"] is True

    def test_negative_sl_rejected(self, backend):
        result = backend.order_send("EURUSD", "buy", 0.01, sl=-1.0)
        assert result["ok"] is False
        assert "positive" in result["error"]

    def test_zero_tp_rejected(self, backend):
        result = backend.order_send("EURUSD", "buy", 0.01, tp=0)
        assert result["ok"] is False
        assert "positive" in result["error"]


class TestSLTPTrigger:
    def test_buy_sl_triggers_close(self, backend):
        r = backend.order_send("EURUSD", "buy", 0.01, sl=1.08500)
        assert r["ok"] is True
        ticket = r["ticket"]

        backend._symbols["EURUSD"]["bid"] = 1.08490
        backend._symbols["EURUSD"]["ask"] = 1.08495
        backend._mark_to_market()

        assert ticket not in backend._positions
        assert backend._deals[0]["comment"] == "SL hit"

    def test_sell_sl_triggers_close(self, backend):
        r = backend.order_send("EURUSD", "sell", 0.01, sl=1.10)
        assert r["ok"] is True
        ticket = r["ticket"]

        backend._symbols["EURUSD"]["bid"] = 1.10005
        backend._symbols["EURUSD"]["ask"] = 1.10015
        backend._mark_to_market()

        assert ticket not in backend._positions
        assert backend._deals[0]["comment"] == "SL hit"

    def test_buy_tp_triggers_close(self, backend):
        r = backend.order_send("EURUSD", "buy", 0.01, tp=1.09)
        assert r["ok"] is True
        ticket = r["ticket"]

        backend._symbols["EURUSD"]["bid"] = 1.09005
        backend._mark_to_market()

        assert ticket not in backend._positions
        assert backend._deals[0]["comment"] == "TP hit"
