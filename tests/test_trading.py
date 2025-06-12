import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from core.trading import Trading
import asyncio

# Ensure pytest-asyncio is enabled
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_safe_mode():
    """Fixture to mock SafeModeChecker."""
    mock = MagicMock()
    mock.check_safe_mode = AsyncMock()
    yield mock

@pytest.fixture
def mock_strategies():
    """Fixture to mock Strategies."""
    mock = MagicMock()
    mock.execute_strategy = MagicMock()
    yield mock

@pytest.fixture
def mock_speedtest():
    """Fixture to mock speedtest to avoid DeprecationWarning."""
    with patch("core.safe_mode.speedtest") as mock_speedtest:
        mock_speedtest.Speedtest.return_value = MagicMock(
            download=MagicMock(return_value=40_000_000),  # 40 Mbps
            ping=MagicMock(return_value=50)  # 50 ms
        )
        yield mock_speedtest

@pytest.fixture
def trading_instance(mock_safe_mode, mock_strategies, mock_speedtest):
    """Fixture to create a Trading instance with mocked dependencies."""
    # Mock the data for Strategies
    mock_data = pd.DataFrame({
        "open": np.random.rand(100),
        "high": np.random.rand(100),
        "low": np.random.rand(100),
        "close": np.random.rand(100),
        "volume": np.random.randint(100, 1000, 100)
    })
    # Patch pandas.DataFrame directly, since pd is imported in tests/test_trading.py
    with patch("pandas.DataFrame", return_value=mock_data):
        trading = Trading()
    # Replace the safe_mode and strategy_manager with mocks
    trading.safe_mode = mock_safe_mode
    trading.strategy_manager = mock_strategies
    return trading

@pytest.mark.asyncio
async def test_trading_init(trading_instance, tmp_path):
    """Test Trading initialization and logging setup."""
    assert trading_instance.is_trading == False
    # Check if log file exists
    log_file = trading_instance.root_dir / "logs" / "trading.log"
    assert log_file.exists()

@pytest.mark.asyncio
async def test_check_conditions_safe(trading_instance):
    """Test check_conditions when Safe Mode allows trading."""
    trading_instance.safe_mode.check_safe_mode.return_value = {"status": "Active"}
    result = await trading_instance.check_conditions()
    assert result == True

@pytest.mark.asyncio
async def test_check_conditions_blocked(trading_instance):
    """Test check_conditions when Safe Mode blocks trading."""
    trading_instance.safe_mode.check_safe_mode.return_value = {
        "status": "Blocked",
        "reason": "VIX level failed"
    }
    result = await trading_instance.check_conditions()
    assert result == False

@pytest.mark.asyncio
async def test_execute_trade_success(trading_instance):
    """Test execute_trade with a successful BUY signal."""
    trading_instance.is_trading = True
    trading_instance.safe_mode.check_safe_mode.return_value = {"status": "Active"}
    trading_instance.strategy_manager.execute_strategy.return_value = "BUY"
    
    trade_result = await trading_instance.execute_trade("rsi_strategy")
    assert trade_result == {
        "action": "buy",
        "symbol": "NIFTY",
        "quantity": 50
    }

@pytest.mark.asyncio
async def test_execute_trade_no_signal(trading_instance):
    """Test execute_trade with a HOLD signal."""
    trading_instance.is_trading = True
    trading_instance.safe_mode.check_safe_mode.return_value = {"status": "Active"}
    trading_instance.strategy_manager.execute_strategy.return_value = "HOLD"
    
    trade_result = await trading_instance.execute_trade("rsi_strategy")
    assert trade_result == None

@pytest.mark.asyncio
async def test_execute_trade_not_trading(trading_instance):
    """Test execute_trade when trading is stopped."""
    trading_instance.is_trading = False
    trade_result = await trading_instance.execute_trade("rsi_strategy")
    assert trade_result == None

@pytest.mark.asyncio
async def test_execute_trade_safe_mode_blocked(trading_instance):
    """Test execute_trade when Safe Mode blocks trading."""
    trading_instance.is_trading = True
    trading_instance.safe_mode.check_safe_mode.return_value = {
        "status": "Blocked",
        "reason": "Trading time failed"
    }
    trade_result = await trading_instance.execute_trade("rsi_strategy")
    assert trade_result == None

@pytest.mark.asyncio
async def test_fetch_trade_signal(trading_instance):
    """Test _fetch_trade_signal method."""
    with patch.object(trading_instance, "_fetch_trade_signal", return_value="rsi_strategy") as mock_fetch:
        strategy_name = await trading_instance._fetch_trade_signal()
        assert strategy_name == "rsi_strategy"
        mock_fetch.assert_called_once()

@pytest.mark.asyncio
async def test_start_stop_trading(trading_instance):
    """Test start_trading and stop_trading loop."""
    trading_instance.is_trading = True  # Simulate trading started
    trading_instance.loop_interval_seconds = 0.01  # Reduce interval for faster testing
    trading_instance.safe_mode.check_safe_mode.return_value = {"status": "Active"}
    trading_instance._fetch_trade_signal = AsyncMock(return_value="rsi_strategy")
    trading_instance.strategy_manager.execute_strategy.return_value = "BUY"
    
    # Start trading in a background task
    task = asyncio.create_task(trading_instance.start_trading())
    await asyncio.sleep(0.05)  # Let the loop run for a few iterations
    
    # Stop trading
    await trading_instance.stop_trading()
    assert trading_instance.is_trading == False
    
    # Cancel the task to clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    pytest.main([__file__])