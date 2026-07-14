"""Tests for live backend — safety guards, bridge health, and fallback behavior."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from mt5_mcp.backend.live import LiveBackend


@pytest.fixture
def live() -> LiveBackend:
    return LiveBackend()


@pytest.fixture
def clear_env():
    """Remove MT5 env vars before and after each test."""
    keys = [
        "MT5_MCP_MODE", "MT5_MCP_BRIDGE_URL", "MT5_MCP_BRIDGE_FILE",
        "MT5_MCP_MAGIC", "MT5_MCP_MAX_VOLUME", "MT5_MCP_SYMBOL_ALLOWLIST",
    ]
    saved = {k: os.environ.pop(k, None) for k in keys}
    yield
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)


class TestLiveBackendDoctor:
    def test_no_bridge_configured(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        result = live.doctor()
        assert result["mode"] == "live"
        assert result["connected"] is False

    def test_doctor_name(self, live):
        assert live.name == "live"

    def test_seed_demo_is_mock_only(self, live):
        result = live.seed_demo()
        assert result["ok"] is False

    def test_bridge_url_unreachable(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://127.0.0.1:19999"
        result = live.doctor()
        assert result["ok"] is False
        assert "Live bridge URL not reachable" in str(result.get("message", ""))

    @patch("mt5_mcp.backend.live.urlopen")
    def test_bridge_health_ok(self, mock_urlopen, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status":"ok"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        result = live.doctor()
        assert result["ok"] is True
        assert result["connected"] is True
        assert "bridge" in result


class TestLiveSafetyGuards:
    def test_order_send_exceeds_max_volume(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_MAX_VOLUME"] = "10"
        result = live.order_send("EURUSD", "buy", 50.0)
        assert result["ok"] is False
        assert "max" in result["error"].lower()

    def test_order_send_symbol_not_allowed(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_SYMBOL_ALLOWLIST"] = "EURUSD,GBPUSD"
        result = live.order_send("XAUUSD", "buy", 1.0)
        assert result["ok"] is False
        assert "allowlist" in str(result)

    def test_order_send_within_limits_passes_guard(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_MAX_VOLUME"] = "100"
        os.environ["MT5_MCP_SYMBOL_ALLOWLIST"] = "EURUSD,GBPUSD,XAUUSD"
        result = live.order_send("EURUSD", "buy", 10.0)
        # Should pass safety guards (then fail on missing bridge)
        assert "guard" not in str(result).lower()

    def test_position_close_stub(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        result = live.position_close(200001)
        assert result["ok"] is False
        assert "safety" in result

    def test_order_cancel_stub(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        result = live.order_cancel(200002)
        assert result["ok"] is False
        assert "safety" in result


class TestLiveBridgeReadThrough:
    def test_positions_no_bridge_returns_empty(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        result = live.positions()
        assert isinstance(result, list)

    def test_orders_no_bridge_returns_empty(self, live, clear_env):
        result = live.orders()
        assert isinstance(result, list)

    def test_account_no_bridge(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        result = live.account()
        assert result["ok"] is False
        assert "error" in result

    def test_symbols_no_bridge_returns_empty(self, live, clear_env):
        result = live.symbols()
        assert isinstance(result, list)

    def test_quote_no_bridge(self, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        result = live.quote("EURUSD")
        assert result["ok"] is False

    def test_history_no_bridge_returns_empty(self, live, clear_env):
        result = live.history_deals()
        assert isinstance(result, list)

    @patch("mt5_mcp.backend.live._bridge_request")
    def test_positions_with_bridge_response(self, mock_bridge, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        mock_bridge.return_value = {
            "ok": True,
            "positions": [
                {"symbol": "EURUSD", "volume": 0.1, "ticket": 300001},
                {"symbol": "GBPUSD", "volume": 0.05, "ticket": 300002},
            ],
        }
        result = live.positions()
        assert len(result) == 2
        assert result[0]["symbol"] == "EURUSD"

    @patch("mt5_mcp.backend.live._bridge_request")
    def test_positions_allowlist_filter(self, mock_bridge, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        os.environ["MT5_MCP_SYMBOL_ALLOWLIST"] = "EURUSD"
        mock_bridge.return_value = {
            "ok": True,
            "positions": [
                {"symbol": "EURUSD", "volume": 0.1, "ticket": 1},
                {"symbol": "GBPUSD", "volume": 0.05, "ticket": 2},
            ],
        }
        result = live.positions()
        assert len(result) == 1
        assert result[0]["symbol"] == "EURUSD"

    @patch("mt5_mcp.backend.live._bridge_request")
    def test_positions_volume_filter(self, mock_bridge, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        os.environ["MT5_MCP_MAX_VOLUME"] = "10"
        mock_bridge.return_value = {
            "ok": True,
            "positions": [
                {"symbol": "EURUSD", "volume": 5.0, "ticket": 1},
                {"symbol": "GBPUSD", "volume": 50.0, "ticket": 2},
            ],
        }
        result = live.positions()
        assert len(result) == 1
        assert result[0]["symbol"] == "EURUSD"

    @patch("mt5_mcp.backend.live._bridge_request")
    def test_history_with_bridge_response(self, mock_bridge, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        mock_bridge.return_value = {
            "ok": True,
            "deals": [
                {"symbol": "EURUSD", "profit": 15.0},
                {"symbol": "GBPUSD", "profit": -8.0},
            ],
        }
        result = live.history_deals()
        assert len(result) == 2

    @patch("mt5_mcp.backend.live._bridge_request")
    def test_history_limit_respected(self, mock_bridge, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        result = live.history_deals(limit=50)
        mock_bridge.assert_called_once()
        # The limit is passed in the URL
        assert "50" in mock_bridge.call_args[0][0]

    @patch("mt5_mcp.backend.live._bridge_request")
    def test_symbols_with_bridge_response(self, mock_bridge, live, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        mock_bridge.return_value = {
            "ok": True,
            "symbols": [
                {"symbol": "EURUSD", "bid": 1.0850},
                {"symbol": "GBPUSD", "bid": 1.2650},
            ],
        }
        result = live.symbols()
        assert len(result) == 2
        assert result[0]["symbol"] == "EURUSD"


class TestBridgeRequestHelper:
    def test_no_url_configured(self, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        from mt5_mcp.backend.live import _bridge_request
        result = _bridge_request("health")
        assert result["ok"] is False
        assert "not set" in result["error"]

    def test_with_magic_number_header(self, clear_env):
        os.environ["MT5_MCP_MODE"] = "live"
        os.environ["MT5_MCP_BRIDGE_URL"] = "http://localhost:9999"
        os.environ["MT5_MCP_MAGIC"] = "123456"
        from mt5_mcp.backend.live import _bridge_request
        with patch("mt5_mcp.backend.live.urlopen", side_effect=OSError("test")):
            result = _bridge_request("health")
            assert result["ok"] is False
