"""Tests for distinct positions vs orders."""

from mt5_mcp.backend import mock_instance, set_mode


def test_positions_empty_after_seed():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    assert len(bk.positions()) == 0


def test_orders_empty_after_seed():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    assert len(bk.orders()) == 0


def test_market_order_creates_position():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    r = bk.order_send("EURUSD", "buy", 0.1, "market")
    assert r.get("ok") is True
    assert len(bk.positions()) == 1
    assert len(bk.orders()) == 0


def test_pending_order_creates_order():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    r = bk.order_send("GBPUSD", "sell", 0.05, "sell_limit", price=1.2700)
    assert r.get("ok") is True
    assert len(bk.positions()) == 0
    assert len(bk.orders()) == 1


def test_close_by_position_id():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    r = bk.order_send("EURUSD", "buy", 0.1, "market")
    ticket = int(r["ticket"])
    close = bk.position_close(ticket)
    assert close.get("ok") is True
    assert len(bk.positions()) == 0
