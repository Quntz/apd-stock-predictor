"""US Stock Predictor Configuration"""

# Stocks + benchmarks
STOCKS = {
    "nvda": {
        "ticker": "NVDA",
        "name": "NVIDIA",
        "benchmark": "QQQ",
        "sector": "Tech"
    },
    "tsla": {
        "ticker": "TSLA",
        "name": "Tesla",
        "benchmark": "QQQ",
        "sector": "Tech"
    },
    "aapl": {
        "ticker": "AAPL",
        "name": "Apple",
        "benchmark": "SPY",
        "sector": "Tech"
    }
}

# Weights: Technical + X Sentiment + Sector
WEIGHTS = {
    "technical": 0.40,
    "x_sentiment": 0.40,
    "sector": 0.20
}

# Signal thresholds
SIGNALS = {
    "buy": 75,
    "hold_min": 50,
    "hold_max": 75,
    "sell": 50
}

# Backtest
BACKTEST = {
    "start_date": "2022-01-01",
    "end_date": "2025-12-31",
    "prediction_window": 5,
}

# Paths
DATA_DIR = "/home/clawdbot/.openclaw/workspace/stock_predictor_us/data"
LOGS_DIR = "/home/clawdbot/.openclaw/workspace/stock_predictor_us/logs"

# Technical indicators
RSI_PERIOD = 14
MA_SHORT = 20
MA_LONG = 60

# X Sentiment API
# Using Stocksera (free tier available) or fallback to mocked sentiment
SENTIMENT_API = "stocksera"  # Options: "stocksera", "mock"
