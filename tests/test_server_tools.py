from mt5_mcp.server import mt5_account, mt5_doctor, mt5_order_send, mt5_seed_demo


def test_tools_json():
    assert "mock" in mt5_doctor()
    assert "ok" in mt5_seed_demo()
    assert "balance" in mt5_account()
    r = mt5_order_send("EURUSD", "buy", 0.05)
    assert "ticket" in r or "ok" in r
