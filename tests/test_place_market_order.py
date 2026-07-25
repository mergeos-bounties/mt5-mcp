"""Tests for mt5_place_market_order with SL/TP validation and stop-out."""

import time

from mt5_mcp.backend import mock_instance, set_mode


def test_place_buy_with_valid_sl_tp():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    # EURUSD ask ~1.08535; SL below, TP above
    result = bk.place_market_order("EURUSD", "buy", 0.10, sl=1.08000, tp=1.09000)
    assert result["ok"] is True
    assert result["retcode"] == 10009
    pos = result["position"]
    assert pos["side"] == "buy"
    assert pos["sl"] == 1.08000
    assert pos["tp"] == 1.09000


def test_place_sell_with_valid_sl_tp():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    # EURUSD bid ~1.08515; SL above, TP below
    result = bk.place_market_order("EURUSD", "sell", 0.10, sl=1.09000, tp=1.08000)
    assert result["ok"] is True
    assert result["retcode"] == 10009


def test_buy_sl_above_entry_rejected():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    # SL 1.09 is above entry (~1.08535)
    result = bk.place_market_order("EURUSD", "buy", 0.10, sl=1.09000, tp=1.10000)
    assert result["ok"] is False
    assert result["retcode"] == 10016
    assert "must be below entry" in result["error"]


def test_buy_tp_below_entry_rejected():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("EURUSD", "buy", 0.10, sl=1.08000, tp=1.08000)
    assert result["ok"] is False
    assert result["retcode"] == 10016
    assert "must be above entry" in result["error"]


def test_sell_sl_below_entry_rejected():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("EURUSD", "sell", 0.10, sl=1.08000, tp=1.07500)
    assert result["ok"] is False
    assert result["retcode"] == 10016
    assert "must be above entry" in result["error"]


def test_sell_tp_above_entry_rejected():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("EURUSD", "sell", 0.10, sl=1.09000, tp=1.09000)
    assert result["ok"] is False
    assert result["retcode"] == 10016
    assert "must be below entry" in result["error"]


def test_unknown_symbol_rejected():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("FAKE", "buy", 0.10, sl=1.08, tp=1.09)
    assert result["ok"] is False
    assert result["retcode"] == 10013


def test_invalid_side_rejected():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("EURUSD", "hold", 0.10, sl=1.08, tp=1.09)
    assert result["ok"] is False
    assert result["retcode"] == 10016


def test_stop_out_long_when_price_falls():
    """Place a buy with SL, then simulate price dropping below SL."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    # Place buy at EURUSD ask (~1.08535) with SL=1.08000
    result = bk.place_market_order("EURUSD", "buy", 0.10, sl=1.08000, tp=1.09000)
    assert result["ok"] is True
    ticket = result["ticket"]
    assert ticket in bk._positions

    # Manually drop EURUSD bid below SL
    bk._symbols["EURUSD"]["bid"] = 1.07900
    bk._symbols["EURUSD"]["ask"] = 1.07920

    # Trigger stop-out check
    deals = bk._check_stop_out()
    assert len(deals) == 1
    assert deals[0]["close_reason"] == "stop_loss"
    assert ticket not in bk._positions


def test_stop_out_long_at_tp():
    """Place a buy with TP, simulate price rising above TP."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("EURUSD", "buy", 0.10, sl=1.08000, tp=1.08600)
    assert result["ok"] is True

    # Push price above TP
    bk._symbols["EURUSD"]["bid"] = 1.08700
    bk._symbols["EURUSD"]["ask"] = 1.08720

    deals = bk._check_stop_out()
    assert len(deals) == 1
    assert deals[0]["close_reason"] == "take_profit"


def test_stop_out_sell_when_price_rises():
    """Place a sell with SL, simulate price rising above SL."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    result = bk.place_market_order("EURUSD", "sell", 0.10, sl=1.09000, tp=1.08000)
    assert result["ok"] is True

    # Push EURUSD ask above SL
    bk._symbols["EURUSD"]["bid"] = 1.09100
    bk._symbols["EURUSD"]["ask"] = 1.09120

    deals = bk._check_stop_out()
    assert len(deals) == 1
    assert deals[0]["close_reason"] == "stop_loss"


def test_place_market_order_rounds_to_digits():
    """SL and TP should be rounded to symbol digit precision."""
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()

    # Pass unrounded SL/TP
    result = bk.place_market_order("EURUSD", "buy", 0.10, sl=1.080004, tp=1.090006)
    assert result["ok"] is True
    pos = result["position"]
    # EURUSD has 5 digits
    assert pos["sl"] == 1.08000
    assert pos["tp"] == 1.09001
