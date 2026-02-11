"""Stocksera API Integration for Real X Sentiment Data

Stocksera provides:
- Real daily mention counts from X (Twitter)
- Sentiment scores (bullish/bearish/neutral)
- Historical data for backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

class StockseraAPI:
    """
    Fetch real X attention/sentiment data from Stocksera.
    
    Free tier: ~5 requests/min, sufficient for backtesting
    """
    
    BASE_URL = "https://api.stocksera.com/api/v1"
    
    def __init__(self, api_key=None):
        """
        Args:
            api_key: Optional Stocksera API key (free tier available without key)
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})
    
    def get_x_mention_data(self, ticker, start_date, end_date):
        """
        Fetch daily X mention counts and sentiment.
        
        Args:
            ticker: Stock ticker (e.g., "NVDA", "TSLA")
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
        
        Returns:
            DataFrame with columns: date, mentions, sentiment_score
        """
        try:
            # Stocksera endpoint for X mentions
            endpoint = f"{self.BASE_URL}/social/twitter"
            params = {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = self.session.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    
                    # Standardize columns
                    rename_map = {
                        'date': 'date',
                        'mentions': 'mentions',
                        'sentiment': 'sentiment_score',
                        'twitter_mentions': 'mentions',
                        'twitter_sentiment': 'sentiment_score'
                    }
                    
                    for old, new in rename_map.items():
                        if old in df.columns and new not in df.columns:
                            df.rename(columns={old: new}, inplace=True)
                    
                    df['date'] = pd.to_datetime(df['date'])
                    df = df[['date', 'mentions', 'sentiment_score']].sort_values('date')
                    
                    return df
            
            print(f"Stocksera API error ({response.status_code}): {ticker}")
            return None
            
        except Exception as e:
            print(f"Error fetching Stocksera data for {ticker}: {e}")
            return None
    
    @staticmethod
    def mock_stocksera_data(ticker, price_series, lead_days=2):
        """
        Generate mock Stocksera data when API unavailable.
        Simulates realistic mention counts leading price.
        
        Args:
            ticker: Stock ticker
            price_series: pd.Series of prices (same index as desired dates)
            lead_days: How many days attention leads price
        
        Returns:
            DataFrame with mock mention data
        """
        n = len(price_series)
        dates = price_series.index if hasattr(price_series, 'index') else pd.date_range('2022-01-01', periods=n)
        
        # Price change leads sentiment
        price_change = price_series.pct_change().fillna(0)
        
        # Attention reacts to price with lead
        attention_signal = price_change.shift(-lead_days).fillna(0)
        
        # Base mentions + signal + noise
        base_mentions = 500
        mentions = base_mentions + attention_signal * base_mentions * 3
        mentions = np.maximum(mentions, 10)  # Minimum 10
        mentions += np.random.normal(0, base_mentions * 0.2, n)  # 20% noise
        mentions = np.maximum(mentions, 10)
        
        # Sentiment (0-100, centered at 50)
        sentiment = 50 + attention_signal * 25
        sentiment = np.clip(sentiment, 0, 100)
        sentiment += np.random.normal(0, 5, n)
        sentiment = np.clip(sentiment, 0, 100)
        
        return pd.DataFrame({
            'date': dates if isinstance(dates, pd.DatetimeIndex) else pd.DatetimeIndex(dates),
            'mentions': mentions,
            'sentiment_score': sentiment
        })


if __name__ == "__main__":
    print("Testing Stocksera Integration...")
    
    api = StockseraAPI()
    
    # Try to fetch real data
    print("\nAttempting to fetch real NVDA X sentiment from Stocksera...")
    data = api.get_x_mention_data("NVDA", "2024-01-01", "2024-12-31")
    
    if data is not None:
        print(f"✓ Fetched {len(data)} rows of real data")
        print(data.head())
    else:
        print("⚠️  Stocksera API unavailable, will use mock data")
        
        # Demo mock data
        prices = 100 + np.cumsum(np.random.normal(0.1, 1, 100))
        price_series = pd.Series(prices)
        
        mock_data = StockseraAPI.mock_stocksera_data("NVDA", price_series)
        print(f"\n✓ Generated mock data ({len(mock_data)} rows)")
        print(mock_data.head())
