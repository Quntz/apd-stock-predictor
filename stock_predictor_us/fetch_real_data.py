#!/usr/bin/env python3
"""
REAL DATA FETCHER - Run this OUTSIDE SANDBOX

Fetches actual EODHD X mention data + real NVIDIA prices
No synthetic data, no cheating
"""

import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime, timedelta
import os
import sys

class RealDataFetcher:
    """Fetch real X data + price data for backtesting"""
    
    def __init__(self, eodhd_key=None):
        self.eodhd_key = eodhd_key or os.getenv("EODHD_API_KEY")
        self.eodhd_url = "https://eodhistoricaldata.com/api"
        
        if not self.eodhd_key:
            print("❌ EODHD_API_KEY not set")
            print("   Set: export EODHD_API_KEY='698beb4f847d90.65238585'")
            sys.exit(1)
    
    def fetch_x_mentions(self, ticker, start_date, end_date):
        """
        Fetch real X mention counts from EODHD
        """
        print(f"Fetching {ticker} X mentions ({start_date} to {end_date})...")
        
        # Try multiple endpoints
        endpoints = [
            f"/alternative-data/tweets-sentiment",
            f"/tweets-sentiment",
            f"/social/twitter"
        ]
        
        params = {
            "s": ticker,
            "from": start_date,
            "to": end_date,
            "api_token": self.eodhd_key
        }
        
        for endpoint in endpoints:
            try:
                url = self.eodhd_url + endpoint
                print(f"  Trying: {endpoint}")
                
                response = requests.get(url, params=params, timeout=30, verify=True)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data)
                        
                        # Normalize column names
                        df.columns = [c.lower() for c in df.columns]
                        
                        # Standardize date column
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                        elif 'publish_date' in df.columns:
                            df['date'] = pd.to_datetime(df['publish_date'])
                            df = df.drop('publish_date', axis=1)
                        
                        # Get mention counts
                        if 'mentions' in df.columns:
                            pass  # Already named correctly
                        elif 'mention_count' in df.columns:
                            df['mentions'] = df['mention_count']
                        elif 'count' in df.columns:
                            df['mentions'] = df['count']
                        
                        df = df[['date', 'mentions']].sort_values('date').dropna()
                        
                        print(f"  ✅ Got {len(df)} rows from {endpoint}")
                        return df
                        
            except Exception as e:
                print(f"  ❌ {endpoint}: {str(e)[:100]}")
                continue
        
        print(f"❌ All EODHD endpoints failed")
        return None
    
    def fetch_prices_yfinance(self, ticker, start_date, end_date):
        """
        Fetch real price data from Yahoo Finance
        """
        print(f"Fetching {ticker} prices ({start_date} to {end_date})...")
        
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if len(df) == 0:
                print(f"❌ No price data for {ticker}")
                return None
            
            # Normalize columns
            df.columns = [c.lower() for c in df.columns]
            df['date'] = df.index
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']].reset_index(drop=True)
            
            print(f"  ✅ Got {len(df)} rows of price data")
            return df
            
        except Exception as e:
            print(f"❌ Price fetch failed: {e}")
            return None
    
    def fetch_prices_csv(self, ticker):
        """
        Fallback: use locally cached CSV if it exists
        """
        local_file = f"{ticker.lower()}_prices.csv"
        
        if os.path.exists(local_file):
            print(f"Loading {ticker} from local cache: {local_file}")
            df = pd.read_csv(local_file)
            print(f"  ✅ Loaded {len(df)} rows")
            return df
        
        return None
    
    def run(self, ticker="NVDA", start_date="2023-01-01", end_date=None):
        """
        Full pipeline: fetch X data + prices
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print("="*70)
        print(f"REAL DATA FETCHER: {ticker}")
        print("="*70)
        
        # Fetch X data
        print("\nStep 1: X Attention Data")
        print("-"*70)
        x_data = self.fetch_x_mentions(ticker, start_date, end_date)
        
        if x_data is None:
            print("⚠️  EODHD X data unavailable (API limit or invalid endpoint)")
            x_data_file = None
        else:
            x_data_file = f"{ticker.lower()}_x_mentions_real.csv"
            x_data.to_csv(x_data_file, index=False)
            print(f"  Saved: {x_data_file}")
            print(f"  Mentions avg: {x_data['mentions'].mean():.0f}")
            print(f"  Date range: {x_data['date'].min().date()} to {x_data['date'].max().date()}")
        
        # Fetch prices
        print("\nStep 2: Price Data")
        print("-"*70)
        price_data = self.fetch_prices_yfinance(ticker, start_date, end_date)
        
        if price_data is None:
            price_data = self.fetch_prices_csv(ticker)
        
        if price_data is None:
            print(f"❌ Could not fetch price data for {ticker}")
            return None, None
        
        price_file = f"{ticker.lower()}_prices_real.csv"
        price_data.to_csv(price_file, index=False)
        print(f"  Saved: {price_file}")
        print(f"  Price range: ${price_data['close'].min():.2f} - ${price_data['close'].max():.2f}")
        print(f"  Date range: {price_data['date'].min().date()} to {price_data['date'].max().date()}")
        
        # Align data
        print("\nStep 3: Align Data")
        print("-"*70)
        
        if x_data is not None:
            # Merge on date
            x_data['date'] = pd.to_datetime(x_data['date']).dt.date
            price_data['date'] = pd.to_datetime(price_data['date']).dt.date
            
            merged = price_data.merge(x_data, on='date', how='inner')
            
            if len(merged) > 0:
                merged_file = f"{ticker.lower()}_aligned_real.csv"
                merged.to_csv(merged_file, index=False)
                print(f"✅ Aligned {len(merged)} matching dates")
                print(f"  Saved: {merged_file}")
                
                # Show correlation
                price_moves = merged['close'].pct_change(5)
                mentions_change = merged['mentions'].pct_change()
                corr = price_moves.corr(mentions_change)
                print(f"  Correlation (5-day price change vs mention change): {corr:+.3f}")
                
                return merged, {
                    'price_file': price_file,
                    'x_file': x_data_file,
                    'merged_file': merged_file
                }
            else:
                print("❌ No matching dates between X data and prices")
                print(f"  X dates: {x_data['date'].min()} to {x_data['date'].max()}")
                print(f"  Price dates: {price_data['date'].min()} to {price_data['date'].max()}")
                return price_data, {
                    'price_file': price_file,
                    'x_file': None,
                    'merged_file': None
                }
        else:
            print("⚠️  X data not available, returning price data only")
            return price_data, {'price_file': price_file}


if __name__ == "__main__":
    fetcher = RealDataFetcher()
    
    # Fetch NVIDIA data
    merged_data, files = fetcher.run(
        ticker="NVDA",
        start_date="2023-01-01",
        end_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    print("\n" + "="*70)
    print("RESULT")
    print("="*70)
    
    if merged_data is not None and len(merged_data) > 0:
        print(f"\n✅ Real data ready for backtesting")
        print(f"   {len(merged_data)} rows of aligned data")
        
        if 'merged_file' in files and files['merged_file']:
            print(f"\nNext step:")
            print(f"  python3 backtest_real_data.py")
    else:
        print(f"\n⚠️  Could not align X and price data")
        print(f"   Check EODHD API key and endpoint availability")
    
    print("="*70)
