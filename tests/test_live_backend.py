import pytest
from mt5_mcp.backend.live import LiveBackend

def test_live_backend_doctor_mock_default():
    b = LiveBackend()
    doc = b.doctor()
    assert doc["mode"] == "live"
    assert "connected" in doc

def test_live_backend_safety_guards():
    b = LiveBackend()
    account = b.account()
    assert "ok" in account
    spec = b.symbol_spec("EURUSD")
    assert "ok" in spec
