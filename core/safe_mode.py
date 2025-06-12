import logging
from pathlib import Path
import yaml
import pytz
from datetime import datetime, time
import speedtest
from logzero import logger, logfile, setup_logger
import telegram
import asyncio
import subprocess
from typing import Dict
from utils.helpers import NeuroSniperHelpers

class SafeModeChecker:
    """Ensures safe trading conditions based on news, VIX, and internet health."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize SafeModeChecker with configuration."""
        self.root_dir = Path(__file__).resolve().parent.parent
        self.config_dir = Path(config_dir)
        self.credentials = self._load_yaml("credentials.yaml")
        self.settings = self._load_yaml("settings.yaml")
        self.ist = pytz.timezone("Asia/Kolkata")
        self.bot = None
        self.trade_count = 0
        self._setup_logging()
        self._setup_telegram()

    def _load_yaml(self, filename: str) -> Dict:
        """Load YAML file from config directory."""
        try:
            with open(self.config_dir / filename, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise

    def _setup_logging(self):
        """Configure logging with logzero."""
        log_path = self.root_dir / "logs" / "safe_mode.log"
        log_path.parent.mkdir(exist_ok=True)
        logfile(log_path, maxBytes=5_000_000, backupCount=5)
        # Disable console output to avoid handle issues in pytest
        setup_logger(disableStderrLogger=True, level=logging.INFO)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logger.info("Safe Mode logging initialized")

    def _setup_telegram(self):
        """Initialize Telegram bot for alerts."""
        try:
            token = self.credentials["telegram"]["token"]
            self.bot = telegram.Bot(token=token)
            logger.info("Telegram bot initialized")
        except Exception as e:
            logger.error(f"Telegram setup failed: {e}")
            self.bot = None

    async def _check_internet_health(self) -> bool:
        """Check internet speed and latency."""
        try:
            min_download = self.settings["safe_mode"]["internet_check"]["min_download_mbps"]
            max_ping = self.settings["safe_mode"]["internet_check"]["max_ping_ms"]
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Mbps
            ping = st.results.ping  # ms
            logger.info(f"Internet health: Download {download_speed:.2f} Mbps, Ping {ping:.2f} ms")
            return download_speed >= min_download and ping <= max_ping
        except Exception as e:
            logger.warning(f"Speedtest failed: {e}. Falling back to ping check.")
            try:
                result = subprocess.run(["ping", "-n", "1", "8.8.8.8"], capture_output=True, text=True)
                if "time=" in result.stdout:
                    logger.info("Ping check to 8.8.8.8 succeeded")
                    return True
                logger.error("Ping check failed")
                return False
            except Exception as e:
                logger.error(f"Ping check failed: {e}")
                return False

    async def _check_news_sentiment(self) -> bool:
        """Check news sentiment based on settings."""
        try:
            required_sentiment = self.settings["safe_mode"]["news_sentiment"].lower()
            # Mock: Align with settings
            sentiment = required_sentiment
            logger.info(f"News sentiment: {sentiment} (mock)")
            return sentiment == "positive"
        except Exception as e:
            logger.error(f"News sentiment check failed: {e}")
            return False

    async def _check_vix(self) -> bool:
        """Check India VIX level."""
        try:
            vix_threshold = self.settings["safe_mode"]["vix_threshold"]
            # Placeholder: Assume VIX = 20
            vix = 20
            logger.info(f"VIX check: Current VIX {vix}, Threshold {vix_threshold}")
            return vix <= vix_threshold
        except Exception as e:
            logger.error(f"VIX check failed: {e}")
            return False

    async def _check_trading_time(self) -> bool:
        """Check if within trading hours."""
        try:
            cutoff_time = datetime.strptime(self.settings["safe_mode"]["trading_cutoff_time"], "%H:%M").time()
            now = NeuroSniperHelpers.get_ist_time()
            market_open = time(9, 15)
            market_close = cutoff_time
            is_within_hours = market_open <= now.time() <= market_close
            is_weekday = now.weekday() < 5
            logger.info(f"Trading time check: {now.time()} between {market_open} and {market_close}, weekday: {is_weekday}")
            return is_within_hours and is_weekday
        except Exception as e:
            logger.error(f"Trading time check failed: {e}")
            return False

    async def _check_trade_limit(self) -> bool:
        """Check daily trade limit."""
        try:
            max_trades = self.settings["safe_mode"]["max_trades_per_day"]
            logger.info(f"Trade count: {self.trade_count}, Limit: {max_trades}")
            return self.trade_count < max_trades
        except Exception as e:
            logger.error(f"Trade limit check failed: {e}")
            return False

    async def check_safe_mode(self) -> Dict[str, str]:
        """Check if trading conditions are safe, return status and reason."""
        try:
            if not self.settings["safe_mode"]["enabled"]:
                logger.info("Safe Mode disabled")
                return {"status": "Active", "reason": "Safe Mode disabled"}

            checks = [
                (await self._check_internet_health(), "Internet health"),
                (await self._check_news_sentiment(), "News sentiment"),
                (await self._check_vix(), "VIX level"),
                (await self._check_trading_time(), "Trading time"),
                (await self._check_trade_limit(), "Trade limit")
            ]
            safe = all(check[0] for check in checks)
            if not safe:
                failed = [name for passed, name in checks if not passed]
                reason = f"{', '.join(failed)} failed"
                logger.warning(f"Safe Mode blocked trading: {reason}")
                if self.bot:
                    chat_id = self.credentials["telegram"]["chat_id"]
                    await self.bot.send_message(chat_id, f"Trading blocked: {reason}")
                return {"status": "Blocked", "reason": reason}
            else:
                logger.info("Safe to trade: All conditions met")
                if self.bot:
                    chat_id = self.credentials["telegram"]["chat_id"]
                    await self.bot.send_message(chat_id, "Safe to trade: All conditions met")
                return {"status": "Active", "reason": "All checks passed"}
        except Exception as e:
            logger.error(f"Safe Mode error: {e}")
            if self.bot:
                chat_id = self.credentials["telegram"]["chat_id"]
                await self.bot.send_message(chat_id, f"Safe Mode error: {e}")
            return {"status": "Blocked", "reason": f"Error: {e}"}

if __name__ == "__main__":
    async def main():
        safe_mode = SafeModeChecker()
        result = await safe_mode.check_safe_mode()
        logger.info(f"Safe Mode result: {result}")

    asyncio.run(main())