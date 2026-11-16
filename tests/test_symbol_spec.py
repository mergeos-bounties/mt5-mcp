import pytest
from mt5_mcp.backend.mock import MockBackend

@pytest.mark.asyncio
async def test_mock_symbol_info_eurusd():
    backend = MockBackend()
    info = await backend.get_symbol_info("EURUSD")
    
    assert info is not None
    assert info["symbol"] == "EURUSD"
    assert info["digits"] == 5
    assert info["lot_step"] == 0.01
    assert info["min_lot"] == 0.01

@pytest.mark.asyncio
async def test_mock_symbol_info_btcusd():
    backend = MockBackend()
    info = await backend.get_symbol_info("BTCUSD")
    
    assert info is not None
    assert info["digits"] == 2
    assert info["lot_step"] == 0.1

@pytest.mark.asyncio
async def test_mock_symbol_not_found():
    backend = MockBackend()
    info = await backend.get_symbol_info("NONEXISTENT")
    
    assert info is None

@pytest.mark.asyncio
async def test_mock_symbol_case_insensitive():
    backend = MockBackend()
    info = await backend.get_symbol_info("eurusd")
    
    assert info is not None
    assert info["symbol"] == "EURUSD"
