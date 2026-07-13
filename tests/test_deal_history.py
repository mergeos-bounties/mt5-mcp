"""Tests for deal history profit breakdown."""

from mt5_mcp.backend import mock_instance, set_mode


def test_history_has_profit_fields():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    deals = bk.history_deals(5)
    assert len(deals) > 0
    for d in deals:
        assert "commission" in d
        assert "swap" in d
        assert "profit" in d


def test_history_limit():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    assert len(bk.history_deals(3)) == 3
    assert len(bk.history_deals(99)) <= 99
