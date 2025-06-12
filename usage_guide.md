NeuroSniper Usage Guide
This guide helps you set up and use the NeuroSniper trading system for intraday derivatives (Nifty, Bank Nifty, Fin Nifty, Midcap Nifty) and weightage stocks (e.g., HDFC Bank, ICICI Bank, TCS, Infosys). Designed for beginners, it aims for no/less loss, maximum profit with features like trap detection, fair value gap (FVG), OI/PCR analysis, and ML learning.
Prerequisites

OS: Windows 11
Python: 3.12.7
IDE: VS Code
Broker: Angel One account with API access
Telegram: Bot token and chat ID for alerts

Setup

Clone or Create Project:

Create directory: D:\AlgoManu\nurosniper
Ensure folder structure:nurosniper/
├── .vscode/
├── config/
├── core/
├── dashboard/
├── data/
├── db/
├── logs/
├── reports/
├── telegram_bot/
├── tests/
├── utils/
├── venv/
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── usage_guide.md
├── pytest.ini




Set Up Virtual Environment:
cd D:\AlgoManu\nurosniper
python -m venv venv
.\venv\Scripts\Activate.ps1


Install Dependencies:
pip install -r requirements.txt


Configure Settings:

Copy config/credentials.yaml.example to config/credentials.yaml:angel_one:
  client_id: "your_client_id"
  password: "your_password"
  api_key: "your_api_key"
telegram:
  token: "your_bot_token"
  chat_id: "your_chat_id"


Edit config/settings.yaml:trading:
  instruments: ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "HDFC BANK", "ICICI BANK", "TCS", "INFOSYS"]
  timeframe: "5min"
  cross_check: "3min"
  max_risk_per_trade: 0.01
  trading_mode: "dry_run"
  strategies: ["rsi_strategy", "fvg_strategy", "seasonality_strategy"]
  ml_model: "auto"





Running the System

Start NeuroSniper:
python main.py


Auto-launches:
Streamlit dashboard (http://localhost:8501)
Telegram bot (sends “System Ready!”)
Market feed, dry run, ML, pre-market report




Command-Line Options:

Pre-market report:python main.py --premarket


Backtest:python main.py --backtest --instrument NIFTY --start-date 2025-05-01 --end-date 2025-06-11





Interacting with the System

Telegram Commands:

/start: Initialize bot
/accept: Accept manual trade signal
/toggle_mode [manual|auto|dry_run]: Switch trading mode
/report [intraday|daily|weekly]: Get performance report
/stop: Stop system


Dashboard:

Open http://localhost:8501
View real-time charts, FVG, OI/PCR, weightage stocks, trap alerts, and reports



Daily Workflow

Pre-Market (~8:30 AM IST):

Run python main.py --premarket
Check Telegram report and dashboard for Nifty trends, OI/PCR, and trap risks
Start system: python main.py


Market Hours (9:15 AM to 3:30 PM IST):

Monitor Telegram for signals (e.g., “Buy NIFTY 22500 CE, Confidence: 92%”)
Use dashboard for FVG, psychological levels, and IV
Respond to danger warnings (e.g., SL hunting)


Post-Market (~4:00 PM IST):

Request reports: /report daily
Backtest: python main.py --backtest
Retrain ML: python utils/ml_engine.py --retrain
Run tests: pytest tests/



Adding New Strategies

Create a strategy in core/strategy_plugins/ (e.g., correlation_strategy.py):from core.strategy_engine import StrategyBase

class CorrelationStrategy(StrategyBase):
    def generate_signal(self, data):
        # Your logic here
        pass


Update config/settings.yaml:strategies:
  - rsi_strategy
  - fvg_strategy
  - correlation_strategy


Watchdog auto-reloads strategy.

Troubleshooting

Logs: Check logs/app.log or logs/market_feed.log
Errors: Ensure API keys are correct in config/credentials.yaml
Tests: Run pytest tests/ to validate components

