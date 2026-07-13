"""Tests for mt5-mcp status."""

from mt5_mcp.backend import get_backend, set_mode, mock_instance


def test_status_fields() -> None:
    set_mode("mock")
    b = get_backend()
    acct = b.account()
    assert acct["ok"] is True
    assert isinstance(acct["balance"], (int, float))
    assert isinstance(acct["equity"], (int, float))
    assert isinstance(acct["positions"], int)
    assert isinstance(acct["pending_orders"], int)
    assert acct["login"] > 0


def test_status_zero_positions_after_seed() -> None:
    set_mode("mock")
    mock_instance().seed_demo()
    acct = mock_instance().account()
    assert acct["positions"] == 0


def test_status_after_order() -> None:
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    bk.order_send("EURUSD", "buy", 0.1, "market")
    acct = bk.account()
    assert acct["positions"] == 1
    assert acct["equity"] > 0
