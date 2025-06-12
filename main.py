import argparse
import logging
import asyncio
import sys
from pathlib import Path
from logzero import logger, logfile
import yaml

# Import completed core modules
from core.trading import Trading
from core.ws_feed import WebSocketFeed
from core.safe_mode import SafeModeChecker

# Set up root directory and logging
ROOT_DIR = Path(__file__).resolve().parent
LOG_PATH = ROOT_DIR / "logs" / "app.log"

def setup_logging():
    """Configure logging with logzero."""
    LOG_PATH.parent.mkdir(exist_ok=True)
    logfile(LOG_PATH, maxBytes=5_000_000, backupCount=5)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logger.info("Main logging initialized")

def load_config(filename: str) -> dict:
    """Load YAML configuration."""
    try:
        with open(ROOT_DIR / "config" / filename, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        raise

async def main_loop(args: argparse.Namespace) -> None:
    """Main async loop to run trading system."""
    try:
        setup_logging()
        logger.info("Starting NeuroSniper trading system")

        # Load configuration
        config = load_config("settings.yaml")
        credentials = load_config("credentials.yaml")

        # Initialize components
        safe_mode = SafeModeChecker()
        trading = Trading()
        ws_feed = WebSocketFeed()

        # Check safe mode
        safe_mode_result = await safe_mode.check_safe_mode()
        if safe_mode_result["status"] != "Active":
            logger.warning(f"Safe Mode blocked trading: {safe_mode_result['reason']}")
            return

        # Start WebSocket feed
        if not await ws_feed.connect():
            logger.error("WebSocket connection failed")
            return

        # Start trading
        await trading.start_trading()

        # Run for 60 seconds (placeholder)
        await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("System shutdown requested")
        if 'ws_feed' in locals():
            await ws_feed.close()
        if 'trading' in locals():
            await trading.stop_trading()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        if 'ws_feed' in locals():
            await ws_feed.close()
        if 'trading' in locals():
            await trading.stop_trading()
        sys.exit(1)

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="NeuroSniper Trading System")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main_loop(args))