import logging
from pathlib import Path
import yaml
from logzero import logger, logfile
from datetime import datetime
import pytz
import subprocess
import socket
from typing import Dict, Optional

class NeuroSniperHelpers:
    """Utility functions for NeuroSniper trading system."""

    @staticmethod
    def setup_logging(log_name: str, root_dir: Optional[Path] = None) -> None:
        """Configure logging with logzero."""
        try:
            if root_dir is None:
                root_dir = Path(__file__).resolve().parent.parent
            log_path = root_dir / "logs" / f"{log_name}.log"
            log_path.parent.mkdir(exist_ok=True)
            logfile(log_path, maxBytes=5_000_000, backupCount=5)
            logging.getLogger().setLevel(logging.INFO)
            logger.info(f"Logging initialized for {log_name}")
        except Exception as e:
            logger.error(f"Failed to setup logging for {log_name}: {e}")
            raise

    @staticmethod
    def load_yaml(filename: str, config_dir: str = "config") -> Dict:
        """Load YAML file from config directory."""
        try:
            config_path = Path(config_dir) / filename
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise

    @staticmethod
    def get_ist_time() -> datetime:
        """Get current time in IST."""
        ist = pytz.timezone("Asia/Kolkata")
        return datetime.now(ist)

    @staticmethod
    def is_market_hours(now: Optional[datetime] = None) -> bool:
        """Check if current time is within Indian market hours (9:15 AM to 3:30 PM IST)."""
        if now is None:
            now = NeuroSniperHelpers.get_ist_time()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_open <= now <= market_close and now.weekday() < 5

    @staticmethod
    def ping_host(host: str, timeout: int = 4) -> bool:
        """Ping a host to check connectivity."""
        try:
            subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout * 1000), host],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"Ping to {host} successful")
            return True
        except subprocess.CalledProcessError:
            logger.warning(f"Ping to {host} failed")
            return False

    @staticmethod
    def check_port(host: str, port: int, timeout: int = 5) -> bool:
        """Check if a port is open on the host."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                logger.info(f"Port {port} on {host} is open")
                return True
        except (socket.timeout, ConnectionRefusedError):
            logger.warning(f"Port {port} on {host} is closed or unreachable")
            return False

if __name__ == "__main__":
    # Example usage
    NeuroSniperHelpers.setup_logging("utils")
    config = NeuroSniperHelpers.load_yaml("settings.yaml")
    now = NeuroSniperHelpers.get_ist_time()
    logger.info(f"Current IST time: {now}")
    logger.info(f"Market hours: {NeuroSniperHelpers.is_market_hours(now)}")
    logger.info(f"Ping 8.8.8.8: {NeuroSniperHelpers.ping_host('8.8.8.8')}")
    logger.info(f"Port check 103.82.178.38:443: {NeuroSniperHelpers.check_port('103.82.178.38', 443)}")