import pytest
import asyncio
from unittest.mock import patch
from datetime import datetime
import pytz
from core.safe_mode import SafeModeChecker
from utils.helpers import NeuroSniperHelpers

@pytest.fixture
def safe_mode():
    """Fixture for SafeModeChecker instance."""
    return SafeModeChecker()

@pytest.fixture
def ist_timezone():
    """Fixture for IST timezone."""
    return pytz.timezone("Asia/Kolkata")

@pytest.mark.asyncio
async def test_safe_mode_vix_high(safe_mode):
    """Test Safe Mode with high VIX."""
    with patch("core.safe_mode.SafeModeChecker._check_vix", return_value=False), \
         patch("core.safe_mode.SafeModeChecker._check_internet_health", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_news_sentiment", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_trading_time", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_trade_limit", return_value=True):
        result = await safe_mode.check_safe_mode()
        assert result["status"] == "Blocked"
        assert "VIX level" in result["reason"]

@pytest.mark.asyncio
async def test_safe_mode_outside_market_hours(safe_mode, ist_timezone):
    """Test Safe Mode outside market hours."""
    outside_time = datetime(2025, 6, 12, 20, 0, tzinfo=ist_timezone)
    with patch("utils.helpers.NeuroSniperHelpers.get_ist_time", return_value=outside_time), \
         patch("core.safe_mode.SafeModeChecker._check_internet_health", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_news_sentiment", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_vix", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_trade_limit", return_value=True):
        result = await safe_mode.check_safe_mode()
        assert result["status"] == "Blocked"
        assert "Trading time" in result["reason"]

@pytest.mark.asyncio
async def test_safe_mode_within_market_hours(safe_mode, ist_timezone):
    """Test Safe Mode within market hours."""
    market_time = datetime(2025, 6, 13, 10, 0, tzinfo=ist_timezone)
    with patch("utils.helpers.NeuroSniperHelpers.get_ist_time", return_value=market_time), \
         patch("core.safe_mode.SafeModeChecker._check_internet_health", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_news_sentiment", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_vix", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_trade_limit", return_value=True):
        result = await safe_mode.check_safe_mode()
        assert result["status"] == "Active"
        assert result["reason"] == "All checks passed"

@pytest.mark.asyncio
async def test_safe_mode_no_internet(safe_mode):
    """Test Safe Mode with no internet."""
    with patch("core.safe_mode.SafeModeChecker._check_internet_health", return_value=False), \
         patch("core.safe_mode.SafeModeChecker._check_news_sentiment", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_vix", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_trading_time", return_value=True), \
         patch("core.safe_mode.SafeModeChecker._check_trade_limit", return_value=True):
        result = await safe_mode.check_safe_mode()
        assert result["status"] == "Blocked"
        assert "Internet health" in result["reason"]

if __name__ == "__main__":
    pytest.main(["-v", __file__])