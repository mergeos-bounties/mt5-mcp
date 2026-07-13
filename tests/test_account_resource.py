"""Tests for mt5://account MCP resource."""

from mt5_mcp.backend import get_backend, set_mode


def test_account_resource_fields():
    set_mode("mock")
    b = get_backend()
    acct = b.account()
    pos = b.positions()
    assert "balance" in acct
    assert "equity" in acct
    assert isinstance(pos, list)
