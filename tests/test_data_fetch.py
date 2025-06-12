import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from core.data_fetch import DataFetch

@pytest.fixture
def data_fetch_instance():
    """Fixture to create a DataFetch instance."""
    return DataFetch()

@pytest.fixture
def mock_data():
    """Fixture for mock market data."""
    return pd.DataFrame({
        "open": np.random.rand(100),
        "high": np.random.rand(100),
        "low": np.random.rand(100),
        "close": np.random.rand(100),
        "volume": np.random.randint(100, 1000, 100)
    })

def test_data_fetch_init(data_fetch_instance):
    """Test DataFetch initialization."""
    assert data_fetch_instance is not None
    # Check if log file exists
    log_file = data_fetch_instance.root_dir / "logs" / "data_fetch.log"
    assert log_file.exists()

def test_fetch_historical_data_success(data_fetch_instance, mock_data):
    """Test fetch_historical_data with a successful response."""
    with patch("core.data_fetch.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": mock_data.to_dict(orient="records")
        }
        mock_get.return_value = mock_response

        symbol = "NIFTY"
        timeframe = "1d"
        result = data_fetch_instance.fetch_historical_data(symbol, timeframe)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100
        assert set(result.columns) == {"open", "high", "low", "close", "volume"}

def test_fetch_historical_data_failure(data_fetch_instance):
    """Test fetch_historical_data with a failed response."""
    with patch("core.data_fetch.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        symbol = "INVALID"
        timeframe = "1d"
        result = data_fetch_instance.fetch_historical_data(symbol, timeframe)
        
        assert result is None

def test_fetch_realtime_data(data_fetch_instance, mock_data):
    """Test fetch_realtime_data with a successful response."""
    with patch("core.data_fetch.websocket.WebSocketApp") as mock_ws:
        # Simulate WebSocket on_message callback
        mock_ws_instance = MagicMock()
        mock_ws.return_value = mock_ws_instance
        
        # Mock the on_message callback to return mock_data
        data_fetch_instance.on_message = MagicMock(return_value=mock_data.iloc[-1].to_dict())
        
        symbol = "NIFTY"
        result = data_fetch_instance.fetch_realtime_data(symbol)
        
        assert isinstance(result, dict)
        assert set(result.keys()) == {"open", "high", "low", "close", "volume"}

if __name__ == "__main__":
    pytest.main([__file__])