"""Backtest: US stocks with X sentiment + technical + sector"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from config import BACKTEST, DATA_DIR, LOGS_DIR, STOCKS
from data_fetcher_us import USDataFetcher
from scoring_us import ScoringEngineUS

class BacktesterUS:
    def __init__(self):
        self.fetcher = USDataFetcher()
        self.engine = ScoringEngineUS()
        os.makedirs(LOGS_DIR, exist_ok=True)
    
    def run_backtest(self, stock_key):
        """Run backtest for a US stock"""
        stock_info = STOCKS[stock_key]
        ticker = stock_info["ticker"]
        benchmark = stock_info["benchmark"]
        
        start_date = BACKTEST["start_date"]
        end_date = BACKTEST["end_date"]
        window = BACKTEST["prediction_window"]
        
        print(f"\n{'='*60}")
        print(f"Backtesting {stock_info['name']} ({ticker})")
        print(f"vs {benchmark} | Period: {start_date} to {end_date}")
        print(f"{'='*60}")
        
        # Fetch data
        print(f"[1/2] Fetching {ticker}...")
        stock_df = self.fetcher.get_stock_data(ticker, start_date, end_date)
        
        print(f"[2/2] Fetching {benchmark}...")
        sector_df = self.fetcher.get_stock_data(benchmark, start_date, end_date)
        
        if stock_df.empty or sector_df.empty:
            print("✗ Error: Could not fetch data")
            return None, None
        
        print(f"✓ Stock: {len(stock_df)} rows | Sector: {len(sector_df)} rows")
        
        # Generate mock X sentiment (correlated with momentum)
        print("Generating X sentiment scores...")
        x_sentiment = self.fetcher.mock_x_sentiment_with_correlation(stock_df, seed_offset=hash(ticker) % 10000)
        
        results = []
        
        # Backtest
        for i in range(60, len(stock_df) - window):
            try:
                current_date = stock_df.iloc[i]['date']
                
                hist_stock = stock_df.iloc[:i+1].copy()
                hist_sector = sector_df.iloc[:i+1].copy()
                
                # Score
                sentiment_score = x_sentiment.iloc[i]
                score_result = self.engine.calculate_alpha_score(
                    hist_stock, hist_sector, sentiment_score
                )
                
                # Actual 5-day excess return
                today_price = stock_df.iloc[i]['close']
                future_price = stock_df.iloc[i + window]['close']
                future_return = (future_price - today_price) / today_price
                
                sector_today = sector_df.iloc[i]['close']
                sector_future = sector_df.iloc[i + window]['close']
                sector_return = (sector_future - sector_today) / sector_today
                
                excess_return = future_return - sector_return
                
                # Check accuracy
                correct = 0
                if score_result["signal"] == "BUY" and excess_return > 0.005:
                    correct = 1
                elif score_result["signal"] == "SELL" and excess_return < -0.005:
                    correct = 1
                elif score_result["signal"] == "HOLD":
                    correct = 1 if abs(excess_return) < 0.02 else 0
                
                results.append({
                    "date": current_date,
                    "alpha_score": score_result["alpha_score"],
                    "signal": score_result["signal"],
                    "technical": score_result["components"]["technical"],
                    "x_sentiment": score_result["components"]["x_sentiment"],
                    "sector": score_result["components"]["sector"],
                    "excess_return": excess_return,
                    "correct": correct
                })
                
            except Exception as e:
                continue
        
        if not results:
            print("✗ No signals generated")
            return None, None
        
        results_df = pd.DataFrame(results)
        metrics = self.calculate_metrics(results_df)
        
        return results_df, metrics
    
    def calculate_metrics(self, results_df):
        """Calculate metrics"""
        buy = results_df[results_df["signal"] == "BUY"]
        sell = results_df[results_df["signal"] == "SELL"]
        hold = results_df[results_df["signal"] == "HOLD"]
        
        excess = results_df["excess_return"]
        
        metrics = {
            "total": len(results_df),
            "buy_count": len(buy),
            "sell_count": len(sell),
            "hold_count": len(hold),
            "accuracy": results_df["correct"].mean(),
            "buy_accuracy": buy["correct"].mean() if len(buy) > 0 else 0,
            "avg_excess": excess.mean(),
            "std_excess": excess.std(),
            "sharpe": (excess.mean() / excess.std() * np.sqrt(252)) if excess.std() > 0 else 0,
        }
        
        return metrics
    
    def print_results(self, metrics, stock_name):
        """Print formatted results"""
        print(f"\nRESULTS: {stock_name}")
        print(f"{'='*40}")
        print(f"Total signals: {metrics['total']}")
        print(f"  Buy: {metrics['buy_count']} | Sell: {metrics['sell_count']} | Hold: {metrics['hold_count']}")
        print(f"\nAccuracy: {metrics['accuracy']:.2%}")
        print(f"  Buy:  {metrics['buy_accuracy']:.2%}")
        print(f"Avg excess return: {metrics['avg_excess']*100:+.3f}%")
        print(f"Sharpe (annualized): {metrics['sharpe']:+.3f}")
        
        if metrics['accuracy'] > 0.50:
            print(f"\n✓ EDGE DETECTED (win rate > 50%)")
        else:
            print(f"\n✗ No edge (win rate ≤ 50%)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("US STOCK BACKTEST - TECHNICAL + X SENTIMENT + SECTOR")
    print("="*60)
    
    backtester = BacktesterUS()
    all_results = {}
    
    for stock_key in ["nvda", "tsla", "aapl"]:
        results_df, metrics = backtester.run_backtest(stock_key)
        
        if metrics:
            stock_name = STOCKS[stock_key]["name"]
            all_results[stock_key] = metrics
            backtester.print_results(metrics, stock_name)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for stock_key, metrics in all_results.items():
        name = STOCKS[stock_key]["name"]
        edge = "✓" if metrics['accuracy'] > 0.50 else "✗"
        print(f"{name:10s}: {edge} Accuracy {metrics['accuracy']:.1%} | Sharpe {metrics['sharpe']:.3f}")
