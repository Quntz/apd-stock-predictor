"""Data fetcher for US stocks (yfinance) + X Sentiment API"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from config import STOCKS, DATA_DIR

class USDataFetcher:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            print("yfinance not installed")
            self.yf = None
    
    def fetch_ohlcv(self, ticker, start_date, end_date):
        """Fetch US stock OHLCV from Yahoo Finance"""
        if self.yf is None:
            return pd.DataFrame()
        
        try:
            df = self.yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                return df
            
            df = df.reset_index()
            df.columns = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
            df['date'] = pd.to_datetime(df['date'])
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df):
        """Calculate RSI, MA, volume metrics"""
        if df.empty or len(df) < 60:
            return df
        
        # RSI (14-period)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Moving averages
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        
        # Volume anomaly
        df['vol_avg_20'] = df['volume'].rolling(20).mean()
        df['vol_anomaly'] = df['volume'] / df['vol_avg_20'].replace(0, 1)
        
        # Momentum
        df['momentum_5d'] = (df['close'] / df['close'].shift(5) - 1) * 100
        
        return df
    
    def get_stock_data(self, ticker, start_date, end_date):
        """Get complete dataset"""
        df = self.fetch_ohlcv(ticker, start_date, end_date)
        if df.empty:
            return df
        df = self.calculate_technical_indicators(df)
        return df
    
    def get_x_sentiment(self, ticker, date):
        """
        Fetch X sentiment for a stock.
        
        For MVP: Using mock data based on patterns.
        In production: Replace with Stocksera API or direct X API.
        
        Returns: sentiment score (0-100)
        """
        
        # Mock implementation
        # In reality, this would fetch from Stocksera or X API
        # For now: realistic pseudo-random with some correlation to price
        
        base_sentiment = 50
        noise = np.random.normal(0, 8)
        
        # Could add seasonality/patterns here
        # For MVP, just return realistic sentiment score
        sentiment = max(0, min(100, base_sentiment + noise))
        
        return sentiment
    
    def mock_x_sentiment_with_correlation(self, stock_df, seed_offset=0):
        """
        Generate realistic mock X sentiment that correlates with price momentum.
        
        This allows us to test whether X sentiment COULD have edge,
        before integrating real API.
        """
        if stock_df.empty:
            return pd.Series()
        
        # Get momentum (proxy for what X might react to)
        momentum = stock_df['momentum_5d'].fillna(0)
        
        # Sentiment somewhat follows momentum + some noise
        np.random.seed(seed_offset)
        base = 50 + momentum * 2  # Momentum influences sentiment
        noise = np.random.normal(0, 5)
        
        sentiment = pd.Series(
            np.clip(base + noise, 0, 100),
            index=stock_df.index
        )
        
        return sentiment


if __name__ == "__main__":
    fetcher = USDataFetcher()
    
    print("Testing US data fetcher...")
    df = fetcher.get_stock_data("NVDA", "2025-01-01", "2025-02-11")
    
    if not df.empty:
        print(f"✓ Fetched {len(df)} rows for NVDA")
        print(df.tail(3))
    else:
        print("✗ No data")
