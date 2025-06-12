import logging
import pandas as pd
import numpy as np
from pathlib import Path

class Strategies:
    def __init__(self, data):
        self.data = data
        self.logger = logging.getLogger("strategies")
        self._setup_logging()

    def _setup_logging(self):
        self.logger.setLevel(logging.DEBUG)
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        handler = logging.FileHandler(log_dir / "strategies.log")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info("Strategies logging initialized")

    def calculate_rsi(self, periods=14):
        """Calculate the Relative Strength Index (RSI) for the given data."""
        if "close" not in self.data.columns:
            self.logger.error("Close price data not available for RSI calculation")
            return 50  # Default to neutral RSI value

        close = self.data["close"]
        delta = close.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=periods).mean()
        avg_loss = loss.rolling(window=periods).mean()

        # Avoid division by zero
        rs = np.where(avg_loss == 0, 100, avg_gain / avg_loss)
        rsi = 100 - (100 / (1 + rs))

        # Return the latest RSI value
        latest_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        self.logger.debug(f"Calculated RSI: {latest_rsi}")
        return latest_rsi

    def execute_strategy(self, strategy_name):
        """Execute the specified trading strategy and return a signal."""
        if strategy_name == "rsi_strategy":
            rsi = self.calculate_rsi()
            if rsi < 30:
                self.logger.info(f"RSI {rsi} < 30, generating BUY signal")
                return "BUY"
            elif rsi > 70:
                self.logger.info(f"RSI {rsi} > 70, generating SELL signal")
                return "SELL"
            else:
                self.logger.info(f"RSI {rsi} between 30 and 70, generating HOLD signal")
                return "HOLD"
        else:
            self.logger.error(f"Unknown strategy: {strategy_name}")
            return "HOLD"