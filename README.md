NeuroSniper Trading System

Overview
NeuroSniper is an automated trading system tailored for the Indian stock market, utilizing Angel One’s API for real-time market data. It combines machine learning for price predictions, technical analysis for signal generation, and robust backtesting to refine trading strategies. Key features include Telegram notifications, a Streamlit dashboard for visualization, and comprehensive logging.
Features



Feature
Description
Files/Folders Involved



Real-Time Market Data
Fetches live data via Angel One’s SmartWebSocketV2.
core/market_feed_api.py, core/angel_api.py


Signal Generation
Generates buy/sell signals using indicators and ML.
core/signal_generator.py, utils/indicators.py, utils/ml_predictor.py


Backtesting
Simulates strategies with historical data.
core/backtester.py, core/historical_data_api.py


Trade Execution
Places orders through Angel One API.
core/trade_executor.py, core/angel_api.py


Risk Management
Manages position sizing and stop-loss.
core/risk_manager.py


Trade Analysis
Evaluates performance metrics.
core/trade_analyzer.py, reports/


Notifications
Sends alerts via Telegram and other channels.
telegram_botapi.py, utils/notifier.py


Dashboard
Visualizes performance with Streamlit.
dashboard/streamlit_app.py


Logging
Centralized logging for debugging.
utils/logger.py, logs/


Utilities
Includes internet monitoring and helpers.
utils/internet_monitor.py, utils/helpers.py


Testing
Unit tests for reliability.
tests/test_backtester.py, tests/test_websocket.py


Project Structure
nurosniper/
├── main.py                   # Main script to run the system
├── requirements.txt          # Dependencies
├── README.md                 # Project overview
├── usage_guide.md            # Setup and usage instructions
├── pytest.ini                # Pytest configuration
├── .gitignore                # Git ignore rules
├── core/                     # Core trading logic
├── tests/                    # Unit tests
├── config/                   # Configuration files
├── utils/                    # Utility modules
├── telegram_bot/             # Telegram bot
├── dashboard/                # Streamlit dashboard
├── logs/                     # Runtime logs
├── data/models/              # ML models
├── db/                       # Database
├── reports/                  # Trade reports
├── .vscode/                  # VS Code settings

Getting Started
See usage_guide.md for detailed setup and usage instructions.
License
For personal use only, not licensed for commercial distribution.
