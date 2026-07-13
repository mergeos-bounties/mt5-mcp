from mt5_mcp.backend.mock import MockBackend
from mt5_mcp.config import set_mode
from mt5_mcp.backend import get_backend


def test_seed_and_symbols():
    b = MockBackend()
    assert b.seed_demo()["ok"]
    assert b.account()["balance"] == 25000.0
    assert any(s["symbol"] == "BTCUSD" for s in b.symbols())


def test_position_roundtrip():
    b = MockBackend()
    b.seed_demo()
    sent = b.order_send("EURUSD", "buy", 0.1, "market")
    assert sent["ok"]
    ticket = sent["ticket"]
    assert any(p["ticket"] == ticket for p in b.positions())
    closed = b.position_close(ticket)
    assert closed["ok"]
    assert b.history_deals(5)


def test_pending_cancel():
    b = MockBackend()
    b.seed_demo()
    pend = b.order_send("GBPUSD", "sell", 0.05, "sell_limit", price=1.27)
    assert pend["ok"]
    assert b.order_cancel(int(pend["ticket"]))["ok"]


def test_get_backend_mock():
    set_mode("mock")
    assert get_backend().name == "mock"
