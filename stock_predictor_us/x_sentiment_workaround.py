"""
X (Twitter) Sentiment Data - Workaround Strategies

Three approaches to get real X mention counts without rate limits:
1. Stocksera API (free, but limited X coverage)
2. Alternative free APIs (EODHD, Finnhub)
3. Cache-based backfilling (batch processing, no rate limits)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class XSentimentWorkaround:
    """
    Strategies to bypass X API rate limits for backtesting.
    """
    
    @staticmethod
    def strategy_1_stocksera():
        """
        Use Stocksera free API which covers:
        - WSB (Wall Street Bets) mentions
        - StockTwits sentiment
        - News sentiment
        - Limited X/Twitter coverage
        
        Installation:
            pip install stocksera
        
        Signup:
            https://stocksera.pythonanywhere.com/accounts/developers/
        
        Free tier:
            - No rate limit mentioned
            - Full historical access
            - No credit card needed
        
        Example:
        ```
        import stocksera
        client = stocksera.Client(api_key="YOUR_API_KEY")
        
        # WSB mentions (Reddit)
        wsb_data = client.wsb_mentions(days=365, ticker="NVDA")
        
        # StockTwits sentiment
        st_data = client.stocktwits(ticker="NVDA")
        
        # News sentiment
        news_data = client.news_sentiment(ticker="NVDA")
        ```
        
        Advantage: Free, no rate limits, easy to use
        Disadvantage: Limited X/Twitter specific data
        """
        pass
    
    @staticmethod
    def strategy_2_eodhd_tweets():
        """
        Use EODHD Tweets Sentiment API.
        
        API: https://eodhd.com/financial-apis-blog/tweets-sentiment-api
        
        Free tier:
            - 250 API calls/day
            - Covers X/Twitter mentions
            - Aggregated daily sentiment
        
        Example:
        ```
        import requests
        
        url = "https://api.eodhd.com/api/tweets-sentiment"
        params = {
            "s": "NVDA",
            "from": "2024-01-01",
            "to": "2024-12-31",
            "api_token": "YOUR_FREE_KEY"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Returns: date, mentions_count, sentiment_score, etc.
        ```
        
        Advantage: Real X/Twitter data, aggregated sentiment
        Disadvantage: 250 calls/day limit (still fast for backtesting)
        """
        pass
    
    @staticmethod
    def strategy_3_batch_caching():
        """
        Intelligent batch processing to avoid rate limits.
        
        Approach:
        1. Download all historical data ONCE (batch request)
        2. Cache locally (CSV/SQLite)
        3. Use cached data for all backtests
        4. Only fetch NEW data daily
        
        Benefits:
        - Zero rate limit issues
        - Fast backtest iteration
        - No API calls during analysis
        
        Pseudocode:
        ```
        # Day 1: Fetch 3 years of data (batch)
        data = fetch_x_mentions("NVDA", "2023-01-01", "2026-02-10")
        data.to_csv("nvda_x_mentions_cache.csv")  # 750 rows
        
        # Days 2-365: Use cache, fetch only new data
        cache = pd.read_csv("nvda_x_mentions_cache.csv")
        new_data = fetch_x_mentions("NVDA", yesterday, today)  # 1 API call
        combined = pd.concat([cache, new_data])
        combined.to_csv("nvda_x_mentions_cache.csv")
        ```
        
        Implementation:
        - Store one CSV per stock
        - Run daily sync job (1 API call = instant)
        - Backtest uses local cache (instant, unlimited)
        """
        
        def create_mention_cache(ticker, start_date, end_date, api_key):
            """
            Fetch and cache historical X mention data.
            Run this ONCE for initial backtest period.
            """
            import requests
            
            # Use EODHD or Stocksera
            url = f"https://api.eodhd.com/api/tweets-sentiment"
            params = {
                "s": ticker,
                "from": start_date,
                "to": end_date,
                "api_token": api_key
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                
                df = pd.DataFrame(data)
                cache_file = f"cache/x_mentions_{ticker}.csv"
                df.to_csv(cache_file, index=False)
                
                print(f"✓ Cached {len(df)} rows for {ticker}")
                return df
                
            except Exception as e:
                print(f"Error caching {ticker}: {e}")
                return None
        
        def sync_mention_cache(ticker, api_key, cache_lookback_days=7):
            """
            Sync cache with new data (daily).
            Only fetches last N days, appends to cache.
            """
            try:
                # Load existing cache
                cache_file = f"cache/x_mentions_{ticker}.csv"
                cache = pd.read_csv(cache_file)
                cache['date'] = pd.to_datetime(cache['date'])
                
                # Fetch new data only
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                today = datetime.now().strftime('%Y-%m-%d')
                
                import requests
                url = f"https://api.eodhd.com/api/tweets-sentiment"
                params = {
                    "s": ticker,
                    "from": yesterday,
                    "to": today,
                    "api_token": api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                new_data = pd.DataFrame(response.json())
                new_data['date'] = pd.to_datetime(new_data['date'])
                
                # Append (deduplicate by date)
                combined = pd.concat([cache, new_data]).drop_duplicates(subset=['date'])
                combined.to_csv(cache_file, index=False)
                
                print(f"✓ Synced {ticker}: {len(combined)} total rows")
                return combined
                
            except Exception as e:
                print(f"Sync error: {e}")
                return None
        
        def get_cached_mentions(ticker, start_date=None, end_date=None):
            """
            Load X mention data from cache (instant, no API calls).
            """
            cache_file = f"cache/x_mentions_{ticker}.csv"
            
            try:
                df = pd.read_csv(cache_file)
                df['date'] = pd.to_datetime(df['date'])
                
                if start_date:
                    df = df[df['date'] >= start_date]
                if end_date:
                    df = df[df['date'] <= end_date]
                
                return df
                
            except FileNotFoundError:
                print(f"Cache not found for {ticker}")
                return None


if __name__ == "__main__":
    print("X Sentiment Data - Workaround Strategies")
    print("="*60)
    
    print("\nRECOMMENDATION: Strategy 3 (Batch Caching)")
    print("- Fetch 3 years of data ONCE via EODHD or Stocksera")
    print("- Cache locally in CSV")
    print("- Use cached data for all backtests (instant, unlimited)")
    print("- Daily sync takes 1 API call (~2 seconds)")
    
    print("\nImplementation Steps:")
    print("1. Get free EODHD API key")
    print("2. Run: fetch_historical('NVDA', '2023-01-01', '2026-02-10')")
    print("3. Store cache locally")
    print("4. Backtest uses cache (no rate limits)")
    print("5. Daily: sync_cache('NVDA') adds yesterday's data")
