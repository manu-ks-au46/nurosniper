import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import yaml
from logzero import logger, logfile
import logging
from typing import Dict
from datetime import datetime
import pytz

class StreamlitDashboard:
    """Streamlit dashboard for NeuroSniper trading system."""

    def __init__(self, config_dir: str = "config"):
        """Initialize dashboard with configuration."""
        self.root_dir = Path(__file__).resolve().parent.parent
        self.config_dir = Path(config_dir)
        self.credentials = self._load_yaml("credentials.yaml")
        self.settings = self._load_yaml("settings.yaml")
        self.ist = pytz.timezone("Asia/Kolkata")
        self._setup_logging()
        self.data = {"timestamp": [], "price": [], "instrument": []}  # Mock data
        st.set_page_config(page_title="NeuroSniper Dashboard", layout="wide")
        if not st.runtime.exists():
            logger.error("Please run this script with 'streamlit run dashboard/streamlit_app.py'")
            st.error("This script must be run with 'streamlit run dashboard/streamlit_app.py'")
            st.stop()

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
        log_path = self.root_dir / "logs" / "dashboard.log"
        log_path.parent.mkdir(exist_ok=True)
        logfile(log_path, maxBytes=5_000_000, backupCount=5)
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logger.info("Dashboard logging initialized")

    def _fetch_data(self):
        """Mock fetching real-time data (to be integrated with ws_feed.py)."""
        try:
            now = datetime.now(self.ist)
            instruments = self.settings["trading"]["instruments"]
            for inst in instruments:
                self.data["timestamp"].append(now)
                self.data["price"].append(10000 + len(self.data["price"]))  # Mock price
                self.data["instrument"].append(inst)
            logger.info("Fetched mock data")
        except Exception as e:
            logger.error(f"Data fetch failed: {e}")

    def run(self):
        """Run the Streamlit dashboard."""
        try:
            logger.info("Starting Streamlit dashboard...")
            st.title("NeuroSniper Trading Dashboard")
            
            # Safe Mode Status
            st.header("Safe Mode Status")
            safe_mode = {"status": "Blocked", "reason": "VIX > 15, Outside trading hours"}  # Mock
            st.write(f"Status: {safe_mode['status']}")
            st.write(f"Reason: {safe_mode['reason']}")

            # Fetch and display data
            if st.button("Refresh Data"):
                self._fetch_data()
            df = pd.DataFrame(self.data)
            if not df.empty:
                st.header("Market Data")
                for inst in df["instrument"].unique():
                    inst_df = df[df["instrument"] == inst]
                    fig = px.line(inst_df, x="timestamp", y="price", title=f"{inst} Price")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No data available. Click 'Refresh Data' to fetch.")

            # Trading Metrics
            st.header("Trading Metrics")
            metrics = {
                "Open Positions": 0,
                "P&L": 0.0,
                "Trades Today": 0
            }
            col1, col2, col3 = st.columns(3)
            col1.metric("Open Positions", metrics["Open Positions"])
            col2.metric("P&L", f"₹{metrics['P&L']:.2f}")
            col3.metric("Trades Today", metrics["Trades Today"])
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            st.error(f"Error: {e}")

if __name__ == "__main__":
    dashboard = StreamlitDashboard()
    dashboard.run()