"""Tests for market orders with SL/TP: validation and stop-out handling."""

import pytest

from mt5_mcp.backend.mock import RETCODE_INVALID_STOPS, MockBackend


@pytest.fixture()
def bk() -> MockBackend:
    b = MockBackend()
    b.seed_demo()
    return b


def test_valid_buy_stops_are_stored_and_rounded(bk: MockBackend) -> None:
    r = bk.order_send("EURUSD", "buy", 0.1, "market", sl=1.07999123, tp=1.09000456)
    assert r["ok"] is True
    pos = r["position"]
    # EURUSD has 5 digits — stops are normalised to the symbol precision.
    assert pos["sl"] == 1.07999
    assert pos["tp"] == 1.09000
    assert bk.positions()[0]["sl"] == 1.07999


def test_buy_sl_above_entry_rejected(bk: MockBackend) -> None:
    r = bk.order_send("EURUSD", "buy", 0.1, "market", sl=1.09, tp=1.10)
    assert r["ok"] is False
    assert r["retcode"] == RETCODE_INVALID_STOPS
    assert "must be below" in r["error"]
    assert bk.positions() == []  # nothing opened


def test_buy_tp_below_entry_rejected(bk: MockBackend) -> None:
    r = bk.order_send("EURUSD", "buy", 0.1, "market", tp=1.07)
    assert r["ok"] is False
    assert r["retcode"] == RETCODE_INVALID_STOPS
    assert bk.positions() == []


def test_sell_stops_are_mirrored(bk: MockBackend) -> None:
    ok = bk.order_send("EURUSD", "sell", 0.1, "market", sl=1.09, tp=1.07)
    assert ok["ok"] is True
    bad = bk.order_send("EURUSD", "sell", 0.1, "market", sl=1.07)
    assert bad["ok"] is False
    assert "must be above" in bad["error"]


def test_stops_level_distance_enforced(bk: MockBackend) -> None:
    spec = bk.symbol_spec("EURUSD")
    assert spec["stops_level"] == 20
    bid = bk.quote("EURUSD")["bid"]
    too_close = round(bid - 5 * spec["point"], spec["digits"])  # 5 points < 20 points
    r = bk.order_send("EURUSD", "buy", 0.1, "market", sl=too_close)
    assert r["ok"] is False
    assert r["retcode"] == RETCODE_INVALID_STOPS
    assert "stops level" in r["error"]
    far_enough = round(bid - 25 * spec["point"], spec["digits"])
    assert bk.order_send("EURUSD", "buy", 0.1, "market", sl=far_enough)["ok"] is True


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.08, 0, "abc"])
def test_non_price_stops_rejected(bk: MockBackend, bad: object) -> None:
    r = bk.order_send("EURUSD", "buy", 0.1, "market", sl=bad)
    assert r["ok"] is False
    assert r["retcode"] == RETCODE_INVALID_STOPS
    assert bk.positions() == []


def test_sl_closes_position_at_stop_price(bk: MockBackend) -> None:
    balance_before = bk.account()["balance"]
    sent = bk.order_send("EURUSD", "buy", 1.0, "market", sl=1.08000, tp=1.09500)
    ticket = sent["ticket"]
    assert len(bk.positions()) == 1

    moved = bk.set_quote("EURUSD", 1.07950, 1.07970)  # gaps through the stop loss
    assert len(moved["closed_by_stops"]) == 1

    assert bk.positions() == []
    deal = bk.history_deals(1)[0]
    assert deal["position_id"] == ticket
    assert deal["reason"] == "sl"
    assert deal["price"] == 1.08000  # filled at the stop, not at the gapped bid
    assert deal["profit"] < 0
    assert bk.account()["balance"] == round(balance_before + deal["profit"], 2)


def test_tp_closes_position_and_books_profit(bk: MockBackend) -> None:
    balance_before = bk.account()["balance"]
    bk.order_send("EURUSD", "buy", 1.0, "market", sl=1.08000, tp=1.09000)
    bk.set_quote("EURUSD", 1.09100, 1.09120)
    assert bk.positions() == []
    deal = bk.history_deals(1)[0]
    assert deal["reason"] == "tp"
    assert deal["price"] == 1.09000
    assert deal["profit"] > 0
    assert bk.account()["balance"] == round(balance_before + deal["profit"], 2)


def test_gap_through_both_levels_fills_the_stop_loss(bk: MockBackend) -> None:
    bk.order_send("EURUSD", "buy", 0.5, "market", sl=1.08000, tp=1.09000)
    # One violent move that covers SL and TP at once — the pessimistic side wins.
    bk.set_quote("EURUSD", 1.07000, 1.09500)
    deal = bk.history_deals(1)[0]
    assert deal["reason"] == "sl"
    assert deal["profit"] < 0


def test_position_without_stops_survives_the_move(bk: MockBackend) -> None:
    bk.order_send("EURUSD", "buy", 0.5, "market")
    bk.set_quote("EURUSD", 1.05000, 1.05020)
    positions = bk.positions()
    assert len(positions) == 1
    assert positions[0]["profit"] < 0  # still floating, just deep in the red


def test_stops_survive_a_partial_close(bk: MockBackend) -> None:
    sent = bk.order_send("EURUSD", "buy", 1.0, "market", sl=1.08000, tp=1.09500)
    ticket = int(sent["ticket"])
    assert bk.position_close(ticket, 0.4)["ok"] is True
    remaining = bk.positions()[0]
    assert remaining["volume"] == pytest.approx(0.6)
    assert remaining["sl"] == 1.08000
    bk.set_quote("EURUSD", 1.07900, 1.07920)
    assert bk.positions() == []
    assert bk.history_deals(1)[0]["volume"] == pytest.approx(0.6)


def test_pending_order_stops_validated_against_pending_price(bk: MockBackend) -> None:
    bad = bk.order_send("GBPUSD", "sell", 0.05, "sell_limit", price=1.2700, sl=1.2600)
    assert bad["ok"] is False
    assert bad["retcode"] == RETCODE_INVALID_STOPS
    assert bk.orders() == []
    good = bk.order_send("GBPUSD", "sell", 0.05, "sell_limit", price=1.2700, sl=1.2750, tp=1.2650)
    assert good["ok"] is True
    assert bk.orders()[0]["sl"] == 1.2750


def test_manual_close_still_reports_reason(bk: MockBackend) -> None:
    sent = bk.order_send("EURUSD", "buy", 0.1, "market")
    closed = bk.position_close(int(sent["ticket"]))
    assert closed["ok"] is True
    assert closed["deal"]["reason"] == "manual"


def test_set_quote_rejects_nonsense(bk: MockBackend) -> None:
    assert bk.set_quote("NOPE", 1.0)["ok"] is False
    assert bk.set_quote("EURUSD", 1.09, 1.08)["ok"] is False  # ask below bid
    assert bk.set_quote("EURUSD", float("nan"))["ok"] is False
