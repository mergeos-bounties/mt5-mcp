"""Tests for live backend behaviour (stubs return structured errors)."""

import os

from mt5_mcp.backend import live_instance, set_mode


def test_live_doctor_no_package():
    """Without MetaTrader5 installed, doctor returns structured error."""
    set_mode("live")
    bk = live_instance()
    result = bk.doctor()
    assert result["mode"] == "live"
    # Either connected (package present) or returns an informative error
    assert "ok" in result
    if not result.get("ok"):
        assert isinstance(result.get("message"), str)


def test_live_seed_demo_rejected():
    """seed_demo is mock-only; live backend rejects it."""
    set_mode("live")
    bk = live_instance()
    result = bk.seed_demo()
    assert result["ok"] is False
    assert "mock-only" in result["error"]


def test_live_account_unavailable():
    """Live account() returns structured error when bridge not configured."""
    set_mode("live")
    bk = live_instance()
    result = bk.account()
    assert result["ok"] is False
    assert isinstance(result["error"], str)


def test_live_order_send_unavailable():
    """Live order_send returns structured error when bridge not configured."""
    set_mode("live")
    bk = live_instance()
    result = bk.order_send("EURUSD", "buy", 0.1)
    assert result["ok"] is False
    assert isinstance(result["error"], str)


def test_live_symbol_spec_unavailable():
    """Live symbol_spec returns structured error when bridge not configured."""
    set_mode("live")
    bk = live_instance()
    result = bk.symbol_spec("EURUSD")
    assert result["ok"] is False


def test_live_place_market_order_unavailable():
    """Live place_market_order returns structured error when bridge not configured."""
    set_mode("live")
    bk = live_instance()
    result = bk.place_market_order("EURUSD", "buy", 0.1, sl=1.08, tp=1.09)
    assert result["ok"] is False
    assert isinstance(result["error"], str)


def test_live_position_close_unavailable():
    """Live position_close returns structured error when bridge not configured."""
    set_mode("live")
    bk = live_instance()
    result = bk.position_close(200001)
    assert result["ok"] is False


def test_live_order_cancel_unavailable():
    """Live order_cancel returns structured error when bridge not configured."""
    set_mode("live")
    bk = live_instance()
    result = bk.order_cancel(200001)
    assert result["ok"] is False
