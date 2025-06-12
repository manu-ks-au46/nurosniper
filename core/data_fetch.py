import logging
import pandas as pd
from pathlib import Path
import requests
import websocket
import json

class DataFetch:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.logger = logging.getLogger("data_fetch")
        self._setup_logging()
        self.api_key = self._load_api_key()

    def _setup_logging(self):
        self.logger.setLevel(logging.DEBUG)
        log_dir = self.root_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        handler = logging.FileHandler(log_dir / "data_fetch.log")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info("DataFetch logging initialized")

    def _load_api_key(self):
        # Placeholder for loading API key (e.g., from config/credentials.yaml)
        return "dummy_api_key"

    def fetch_historical_data(self, symbol, timeframe):
        """Fetch historical data for the given symbol and timeframe."""
        try:
            url = f"https://api.example.com/historical?symbol={symbol}&timeframe={timeframe}&api_key={self.api_key}"
            self.logger.info(f"Fetching historical data from {url}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json().get("data", [])
                df = pd.DataFrame(data)
                self.logger.info(f"Fetched {len(df)} rows of historical data for {symbol}")
                return df
            else:
                self.logger.error(f"Failed to fetch historical data: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            return None

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            self.logger.debug(f"Received WebSocket message: {data}")
            return data
        except Exception as e:
            self.logger.error(f"Error processing WebSocket message: {e}")
            return None

    def on_error(self, ws, error):
        """Handle WebSocket errors."""
        self.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closure."""
        self.logger.info("WebSocket closed")

    def on_open(self, ws):
        """Handle WebSocket opening."""
        self.logger.info("WebSocket opened")

    def fetch_realtime_data(self, symbol):
        """Fetch real-time data for the given symbol via WebSocket."""
        try:
            ws_url = f"ws://api.example.com/realtime?symbol={symbol}&api_key={self.api_key}"
            self.logger.info(f"Connecting to WebSocket: {ws_url}")
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            # Simulate a single message for testing purposes
            # In a real scenario, this would run in a loop or separate thread
            message = json.dumps({
                "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000
            })
            result = self.on_message(ws, message)
            return result
        except Exception as e:
            self.logger.error(f"Error fetching real-time data: {e}")
            return None