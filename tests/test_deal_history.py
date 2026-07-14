"""Tests for deal history profit breakdown and pagination."""

from typer.testing import CliRunner

from mt5_mcp.backend import mock_instance, set_mode
from mt5_mcp.cli import app

runner = CliRunner()


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


def test_history_paginates_with_offset():
    set_mode("mock")
    bk = mock_instance()
    bk.seed_demo()
    first_page = bk.history_deals(limit=2, offset=0)
    second_page = bk.history_deals(limit=2, offset=2)
    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {d["ticket"] for d in first_page}.isdisjoint({d["ticket"] for d in second_page})


def test_history_cli_demo_supports_offset():
    r = runner.invoke(app, ["call", "history_deals", "limit=2", "offset=1"])
    assert r.exit_code == 0
    assert "demo-history-2" in r.stdout
    assert "demo-history-3" not in r.stdout
