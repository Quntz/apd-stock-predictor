# US Stock Predictor - X Sentiment Edition

Predict 5-day excess return using **Technical + X Sentiment + Sector**.

## Stocks
- **NVIDIA (NVDA)** vs QQQ (Nasdaq 100 ETF)
- **Tesla (TSLA)** vs QQQ
- **Apple (AAPL)** vs SPY (S&P 500 ETF)

## Data Sources
- **Price/OHLCV:** Yahoo Finance (yfinance)
- **Sector ETF:** Yahoo Finance
- **X Sentiment:** Twitter API v2 (or web scraping)

## Scoring Model
```
AlphaScore = 0.40 * Technical + 0.40 * X_Sentiment + 0.20 * Sector
Signal: Buy (>75), Hold (50-75), Sell (<50)
```

## Status
- [ ] Data fetcher (yfinance + X scraper)
- [ ] Sentiment engine (X data processing)
- [ ] Technical scoring
- [ ] Backtest (2022-2025)
- [ ] Daily runner + alerts
