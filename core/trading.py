import logging
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from core.safe_mode import SafeModeChecker
from core.strategies import Strategies

class Trading:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent  # Adjusted to D:\AlgoManu\nurosniper
        # Ensure logs directory exists
        log_dir = self.root_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("trading")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_dir / "trading.log")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info("Trading logging initialized")

        self.is_trading = False
        self.loop_interval_seconds = 1  # Default loop interval: 1 second
        self.safe_mode = SafeModeChecker()
        
        # Mock data for Strategies (for testing purposes)
        mock_data = pd.DataFrame({
            "open": np.random.rand(100),
            "high": np.random.rand(100),
            "low": np.random.rand(100),
            "close": np.random.rand(100),
            "volume": np.random.randint(100, 1000, 100)
        })
        self.strategy_manager = Strategies(data=mock_data)  # Pass mock_data to Strategies

    async def check_conditions(self):
        result = await self.safe_mode.check_safe_mode()
        if result["status"] == "Active":
            self.logger.info("Trading conditions met")
            return True
        else:
            self.logger.warning(f"Trading blocked: {result['reason']}")
            return False

    async def execute_trade(self, strategy_name):
        if not self.is_trading:
            self.logger.warning("Trading is stopped")
            return None

        if not await self.check_conditions():
            return None

        signal = self.strategy_manager.execute_strategy(strategy_name)
        if signal == "BUY":
            trade_result = {
                "action": "buy",
                "symbol": "NIFTY",
                "quantity": 50
            }
            self.logger.info(f"Trade executed: {trade_result}")
            return trade_result
        elif signal == "SELL":
            trade_result = {
                "action": "sell",
                "symbol": "NIFTY",
                "quantity": 50
            }
            self.logger.info(f"Trade executed: {trade_result}")
            return trade_result
        else:
            self.logger.debug(f"No trade executed: Signal={signal}")
            return None

    async def _fetch_trade_signal(self):
        # Placeholder for fetching the strategy name
        return "rsi_strategy"

    async def start_trading(self):
        self.is_trading = True
        self.logger.info("Trading started")
        try:
            while self.is_trading:
                if await self.check_conditions():
                    strategy_name = await self._fetch_trade_signal()
                    await self.execute_trade(strategy_name)
                await asyncio.sleep(self.loop_interval_seconds)
        except Exception as e:
            self.logger.error(f"Trading loop failed: {str(e)}")
            await self.stop_trading()

    async def stop_trading(self):
        self.is_trading = False
        self.logger.info("Trading stopped")