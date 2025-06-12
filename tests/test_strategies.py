import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from core.strategies import Strategies

# Mock data for tests
@pytest.fixture
def mock_data():
    return pd.DataFrame({
        "open": np.random.rand(100),
        "high": np.random.rand(100),
        "low": np.random.rand(100),
        "close": np.random.rand(100),
        "volume": np.random.randint(100, 1000, 100)
    })

@pytest.fixture
def strategies_instance(mock_data):
    """Fixture to create a Strategies instance."""
    return Strategies(data=mock_data)

def test_strategies_init(strategies_instance, mock_data):
    """Test Strategies initialization."""
    assert strategies_instance.data.equals(mock_data)
    assert len(strategies_instance.data) == 100

def test_execute_strategy_rsi_buy(strategies_instance):
    """Test execute_strategy with RSI strategy returning BUY."""
    # Mock RSI calculation to return a value < 30 (BUY signal)
    with patch.object(strategies_instance, "calculate_rsi", return_value=25):
        signal = strategies_instance.execute_strategy("rsi_strategy")
        assert signal == "BUY"

def test_execute_strategy_rsi_sell(strategies_instance):
    """Test execute_strategy with RSI strategy returning SELL."""
    # Mock RSI calculation to return a value > 70 (SELL signal)
    with patch.object(strategies_instance, "calculate_rsi", return_value=75):
        signal = strategies_instance.execute_strategy("rsi_strategy")
        assert signal == "SELL"

def test_execute_strategy_rsi_hold(strategies_instance):
    """Test execute_strategy with RSI strategy returning HOLD."""
    # Mock RSI calculation to return a value between 30 and 70 (HOLD signal)
    with patch.object(strategies_instance, "calculate_rsi", return_value=50):
        signal = strategies_instance.execute_strategy("rsi_strategy")
        assert signal == "HOLD"

def test_execute_strategy_invalid(strategies_instance):
    """Test execute_strategy with an invalid strategy name."""
    signal = strategies_instance.execute_strategy("invalid_strategy")
    assert signal == "HOLD"  # Default to HOLD for unknown strategies

if __name__ == "__main__":
    pytest.main([__file__])