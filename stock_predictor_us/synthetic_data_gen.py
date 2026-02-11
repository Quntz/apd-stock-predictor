"""Generate realistic synthetic market data for model validation"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import STOCKS

def generate_synthetic_stock_data(ticker, start_date, end_date, seed=None):
    """
    Generate realistic synthetic OHLCV data.
    Includes: trends, mean reversion, volatility clustering, correlations.
    """
    if seed is not None:
        np.random.seed(seed)
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    dates = pd.bdate_range(start=start, end=end)
    
    n = len(dates)
    
    # Starting price (realistic)
    prices = {
        "NVDA": 25,
        "TSLA": 900,
        "AAPL": 120,
        "QQQ": 280,
        "SPY": 360
    }
    
    start_price = prices.get(ticker, 100)
    
    # Generate returns with realistic properties
    drift = 0.0003  # Small daily drift
    volatility = 0.015  # ~2.4% annualized
    
    # AR(1) process for volatility clustering
    vol_process = np.zeros(n)
    vol_process[0] = volatility
    for i in range(1, n):
        vol_process[i] = 0.7 * vol_process[i-1] + 0.3 * volatility + np.random.normal(0, 0.001)
    vol_process = np.abs(vol_process)
    
    # Generate returns
    returns = np.random.normal(drift, 1) * vol_process
    
    # Add trending periods
    for period_start in range(0, n, 252//4):  # ~quarterly trends
        trend_direction = np.random.choice([-1, 0, 1])
        trend_length = np.random.randint(20, 60)
        for j in range(period_start, min(period_start + trend_length, n)):
            returns[j] += trend_direction * 0.001
    
    # Generate prices
    prices_array = np.zeros(n)
    prices_array[0] = start_price
    for i in range(1, n):
        prices_array[i] = prices_array[i-1] * (1 + returns[i])
    
    # Generate OHLC
    close = prices_array
    high = prices_array * (1 + np.abs(np.random.normal(0, vol_process)))
    low = prices_array * (1 - np.abs(np.random.normal(0, vol_process)))
    open_price = prices_array * (1 + np.random.normal(0, vol_process / 2))
    
    # Ensure OHLC order
    high = np.maximum(np.maximum(high, open_price), close)
    low = np.minimum(np.minimum(low, open_price), close)
    
    # Volume (random but realistic)
    volume = np.random.uniform(10_000_000, 100_000_000, n)
    
    df = pd.DataFrame({
        'date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    # Add technical indicators
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    df['vol_avg_20'] = df['volume'].rolling(20).mean()
    df['vol_anomaly'] = df['volume'] / df['vol_avg_20'].replace(0, 1)
    
    df['momentum_5d'] = (df['close'] / df['close'].shift(5) - 1) * 100
    
    return df.dropna()


def generate_correlated_pair(stock_ticker, benchmark_ticker, start_date, end_date):
    """
    Generate stock and benchmark with realistic correlation.
    Benchmark moves slower, stock is more volatile but correlated.
    """
    # Generate benchmark first
    bench_df = generate_synthetic_stock_data(benchmark_ticker, start_date, end_date, seed=42)
    
    # Generate stock with correlation to benchmark
    np.random.seed(hash(stock_ticker) % 10000)
    
    bench_returns = bench_df['close'].pct_change().fillna(0)
    
    # Stock returns = 0.7 * benchmark + 0.3 * idiosyncratic
    stock_idiosyncratic = np.random.normal(0.0003, 0.02, len(bench_df))
    
    # Align returns with benchmark
    bench_returns_full = np.zeros(len(bench_df))
    bench_returns_full[1:] = bench_returns.values
    
    stock_returns = 0.7 * bench_returns_full + 0.3 * stock_idiosyncratic
    
    # Build stock prices
    start_price = {
        "NVDA": 25,
        "TSLA": 900,
        "AAPL": 120,
    }.get(stock_ticker, 100)
    
    prices = np.zeros(len(bench_df))
    prices[0] = start_price
    for i in range(1, len(prices)):
        prices[i] = prices[i-1] * (1 + stock_returns[i])
    
    # Generate OHLC
    volatility = np.abs(stock_returns) * 2
    high = prices * (1 + np.abs(np.random.normal(0, volatility.mean() / 2, len(prices))))
    low = prices * (1 - np.abs(np.random.normal(0, volatility.mean() / 2, len(prices))))
    open_price = prices * (1 + np.random.normal(0, volatility.mean() / 3, len(prices)))
    
    high = np.maximum(np.maximum(high, open_price), prices)
    low = np.minimum(np.minimum(low, open_price), prices)
    
    df = pd.DataFrame({
        'date': bench_df['date'],
        'open': open_price,
        'high': high,
        'low': low,
        'close': prices,
        'volume': np.random.uniform(10_000_000, 100_000_000, len(prices))
    })
    
    # Add technicals
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['vol_avg_20'] = df['volume'].rolling(20).mean()
    df['vol_anomaly'] = df['volume'] / df['vol_avg_20'].replace(0, 1)
    df['momentum_5d'] = (df['close'] / df['close'].shift(5) - 1) * 100
    
    return df.dropna(), bench_df


if __name__ == "__main__":
    print("Generating synthetic data for backtest validation...")
    
    stock_df, bench_df = generate_correlated_pair("NVDA", "QQQ", "2022-01-01", "2025-12-31")
    
    print(f"✓ Generated {len(stock_df)} rows")
    print(f"  Stock price range: ${stock_df['close'].min():.2f} - ${stock_df['close'].max():.2f}")
    print(f"  Benchmark range: ${bench_df['close'].min():.2f} - ${bench_df['close'].max():.2f}")
    print(stock_df.tail())
