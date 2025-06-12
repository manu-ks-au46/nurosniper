import yaml
import logging
from pathlib import Path
import pyotp
from SmartApi import SmartConnect, SmartWebSocket
from logzero import logger, logfile
import asyncio
from datetime import datetime, time
import pytz
import socket
import signal
import sys

class PatchedSmartWebSocket(SmartWebSocket):
    """Patched SmartWebSocket to handle IP fallback and callback fix."""
    
    def __init__(self, feed_token, client_code, host="smartapisocket.angelone.in"):
        self._host = host
        super().__init__(feed_token, client_code)
        
    def _on_close(self, ws, *args, **kwargs):
        """Handle WebSocket closure with flexible arguments."""
        logger.debug(f"WebSocket closed with args: {args}, kwargs: {kwargs}")
        logger.info("WebSocket closed")
        
    def connect(self):
        """Override connect to use resolved IPv4 host with retries."""
        fallback_ips = ["103.82.178.35", "103.82.178.36", "103.82.178.37", "103.82.178.38", "103.82.178.39"]
        resolved_host = None
        
        for ip in [self._host] + fallback_ips:
            for _ in range(3):  # Retry DNS 3 times
                try:
                    resolved_host = socket.gethostbyname(ip)
                    logger.info(f"Resolved {ip} to {resolved_host} (IPv4)")
                    break
                except socket.gaierror as e:
                    logger.warning(f"DNS resolution failed for {ip}: {e}")
                    asyncio.sleep(1)
            if resolved_host:
                break
        
        if not resolved_host:
            resolved_host = "103.82.178.39"
            logger.error("All DNS resolutions failed, using fallback IP 103.82.178.39")

        self._ws_url = f"wss://{resolved_host}/smart-stream"
        try:
            socket.create_connection((resolved_host, 443), timeout=5)
            logger.info(f"TCP connection to {resolved_host}:443 successful")
            super().connect()
        except Exception as e:
            logger.error(f"WebSocket connect failed for {resolved_host}: {e}")
            raise

class WebSocketFeed:
    """Manages WebSocket connection for real-time market data."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize WebSocketFeed with configuration."""
        self.root_dir = Path(__file__).resolve().parent.parent
        self.config_dir = Path(config_dir)
        self.credentials = self._load_yaml("credentials.yaml")
        self.settings = self._load_yaml("settings.yaml")
        self.api = None
        self.ws = None
        self._setup_logging()
        self.ist = pytz.timezone("Asia/Kolkata")
        self.max_retries = 5
        self.retry_delay = 10  # seconds
        self.ws_host = "smartapisocket.angelone.in"
        self._setup_signal_handlers()

    def _load_yaml(self, filename: str) -> dict:
        """Load YAML file from config directory."""
        try:
            with open(self.config_dir / filename, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise

    def _setup_logging(self):
        """Configure logging with logzero."""
        log_path = self.root_dir / "logs" / "ws_feed.log"
        log_path.parent.mkdir(exist_ok=True)
        logfile(log_path, maxBytes=5_000_000, backupCount=5)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("websocket").setLevel(logging.DEBUG)
        logger.info("WebSocketFeed logging initialized")

    def _setup_signal_handlers(self):
        """Handle Ctrl+C gracefully."""
        def signal_handler(sig, frame):
            logger.info("Received interrupt signal, closing WebSocket...")
            asyncio.create_task(self.close())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)

    def _is_market_hours(self):
        """Check if current time is within market hours (9:15 AM–3:30 PM IST)."""
        now = datetime.now(self.ist)
        market_open = time(9, 15)
        market_close = time(15, 30)
        return market_open <= now.time() <= market_close and now.weekday() < 5

    async def authenticate(self):
        """Authenticate with Angel One SmartAPI."""
        try:
            angelone_creds = self.credentials.get("angelone", {})
            client_id = angelone_creds.get("client_id")
            password = angelone_creds.get("password")
            api_key = angelone_creds.get("api_key")
            totp_secret = angelone_creds.get("totp_secret")

            if not all([client_id, password, api_key, totp_secret]):
                missing = [k for k, v in {"client_id": client_id, "password": password, "api_key": api_key, "totp_secret": totp_secret}.items() if not v]
                raise ValueError(f"Missing credentials: {', '.join(missing)}")

            self.api = SmartConnect(api_key=api_key)
            totp = pyotp.TOTP(totp_secret).now()
            data = self.api.generateSession(client_id, password, totp)

            if data["status"]:
                logger.info(f"Authenticated successfully for {client_id}")
            else:
                logger.error(f"Authentication failed: {data['message']}")
                raise Exception("Authentication failed")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    async def check_network(self):
        """Check network connectivity."""
        try:
            resolved_host = socket.gethostbyname(self.ws_host)
            socket.create_connection((resolved_host, 443), timeout=5)
            logger.info(f"Network connectivity confirmed: {self.ws_host} ({resolved_host})")
            return True
        except Exception as e:
            logger.error(f"Network check failed: {e}")
            return False

    async def connect(self):
        """Connect to SmartAPI WebSocket with retries."""
        if not self._is_market_hours():
            logger.warning("Outside market hours (9:15 AM–3:30 PM IST). WebSocket may not connect.")
            return False  # Block non-market hours

        if not self.api:
            await self.authenticate()

        if not await self.check_network():
            raise Exception("Network unavailable")

        for attempt in range(self.max_retries):
            try:
                feed_token = self.api.getfeedToken()
                client_code = self.credentials["angelone"]["client_id"]
                self.ws = PatchedSmartWebSocket(feed_token, client_code, host=self.ws_host)

                def on_message(ws, message):
                    logger.info(f"WebSocket message: {message}")

                def on_open(ws):
                    logger.info("WebSocket connected")
                    self._subscribe()

                def on_error(ws, error):
                    logger.error(f"WebSocket error: {error}")

                self.ws.on_message = on_message
                self.ws.on_open = on_open
                self.ws.on_error = on_error
                self.ws.on_close = self.ws._on_close

                self.ws.connect()
                logger.info("WebSocket connection initiated")
                return True
            except Exception as e:
                logger.error(f"WebSocket connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached. WebSocket connection failed.")
                    raise
        return False

    def _subscribe(self):
        """Subscribe to instruments."""
        try:
            instruments = self.settings["trading"]["instruments"]
            tokens = [self._get_symbol(instrument) for instrument in instruments]
            self.ws.subscribe("ORDER", tokens)
            logger.info(f"Subscribed to instruments: {instruments}")
        except Exception as e:
            logger.error(f"Subscription error: {e}")

    def _get_symbol(self, instrument: str) -> str:
        """Fetch symbol token for instrument."""
        token_map = {
            "NIFTY": "99926000",
            "BANKNIFTY": "99926009",
            "FINNIFTY": "99926037",
            "MIDCPNIFTY": "99926074"
        }
        return token_map.get(instrument, "0")

    async def close(self):
        """Gracefully close WebSocket connection."""
        if self.ws and hasattr(self.ws, '_ws') and self.ws._ws:
            try:
                self.ws._ws.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

if __name__ == "__main__":
    async def main():
        ws_feed = WebSocketFeed()
        try:
            await ws_feed.connect()
            await asyncio.sleep(60)  # Run for 60 seconds
        except KeyboardInterrupt:
            logger.info("Main function interrupted by keyboard, closing...")
        finally:
            await ws_feed.close()

    asyncio.run(main())