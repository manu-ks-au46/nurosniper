import logging
from pathlib import Path
import yaml
from logzero import logger, logfile
from telegram.ext import Application, CommandHandler
import asyncio
import signal
import sys
from typing import Dict

class TelegramBotCommander:
    """Manages Telegram bot commands and alerts for NeuroSniper."""

    def __init__(self, config_dir: str = "config"):
        """Initialize Telegram bot with configuration."""
        self.root_dir = Path(__file__).resolve().parent.parent
        self.config_dir = Path(config_dir)
        self.credentials = self._load_yaml("credentials.yaml")
        self.settings = self._load_yaml("settings.yaml")
        self.bot = None
        self.app = None
        self.is_trading = False
        self._setup_logging()
        self._setup_signal_handlers()

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
        log_path = self.root_dir / "logs" / "telegram_bot.log"
        log_path.parent.mkdir(exist_ok=True)
        logfile(log_path, maxBytes=5_000_000, backupCount=5)
        logging.getLogger("telegram").setLevel(logging.WARNING)
        logger.info("Telegram bot logging initialized")

    def _setup_signal_handlers(self):
        """Handle Ctrl+C gracefully."""
        def signal_handler(sig, frame):
            logger.info("Received interrupt signal, shutting down bot...")
            if self.app:
                # Schedule shutdown tasks
                asyncio.create_task(self.app.stop())
                asyncio.create_task(self.app.shutdown())
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)

    async def _send_alert(self, message: str):
        """Send alert to Telegram chat."""
        try:
            if self.settings["telegram"]["alerts_enabled"]:
                chat_id = self.credentials["telegram"]["chat_id"]
                await self.app.bot.send_message(chat_id=chat_id, text=message)
                logger.info(f"Sent alert: {message}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    async def start_command(self, update, context):
        """Handle /start command."""
        try:
            self.is_trading = True
            message = "NeuroSniper trading started."
            await update.message.reply_text(message)
            await self._send_alert(message)
        except Exception as e:
            logger.error(f"Start command failed: {e}")
            await update.message.reply_text(f"Error: {e}")

    async def stop_command(self, update, context):
        """Handle /stop command."""
        try:
            self.is_trading = False
            message = "NeuroSniper trading stopped."
            await update.message.reply_text(message)
            await self._send_alert(message)
        except Exception as e:
            logger.error(f"Stop command failed: {e}")
            await update.message.reply_text(f"Error: {e}")

    async def status_command(self, update, context):
        """Handle /status command."""
        try:
            status = "running" if self.is_trading else "stopped"
            message = f"NeuroSniper status: {status}"
            await update.message.reply_text(message)
            logger.info(f"Status requested: {status}")
        except Exception as e:
            logger.error(f"Status command failed: {e}")
            await update.message.reply_text(f"Error: {e}")

    async def start(self):
        """Start the Telegram bot."""
        try:
            token = self.credentials["telegram"]["token"]
            self.app = Application.builder().token(token).build()
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("stop", self.stop_command))
            self.app.add_handler(CommandHandler("status", self.status_command))
            logger.info("Starting Telegram bot...")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            logger.info("Telegram bot running")
            while True:
                await asyncio.sleep(3600)  # Keep bot running
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            raise

    async def send_trade_alert(self, trade_info: Dict):
        """Send trade execution alert."""
        if "trade_execution" in self.settings["telegram"]["alert_types"]:
            message = f"Trade executed: {trade_info}"
            await self._send_alert(message)

    async def send_safe_mode_alert(self, reason: str):
        """Send Safe Mode trigger alert."""
        if "safe_mode_trigger" in self.settings["telegram"]["alert_types"]:
            message = f"Safe Mode triggered: {reason}"
            await self._send_alert(message)

    async def send_system_health_alert(self, status: str):
        """Send system health alert."""
        if "system_health" in self.settings["telegram"]["alert_types"]:
            message = f"System health: {status}"
            await self._send_alert(message)

if __name__ == "__main__":
    async def main():
        bot = TelegramBotCommander()
        await bot.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # asyncio.run() handles cleanup automatically