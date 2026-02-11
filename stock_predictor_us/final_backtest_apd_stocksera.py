"""FINAL BACKTEST: APD with Real Stocksera Data + Relaxed Thresholds"""

import pandas as pd
import numpy as np
from config import BACKTEST
from stocksera_integration import StockseraAPI
from scoring_apd_v2 import ScoringEngineAPDv2
from apd_feature import APDFeatureEngine

def generate_realistic_data(n=984, start_price=50, volatility=0.015):
    """Generate realistic stock data"""
    dates = pd.date_range('2022-01-01', periods=n)
    drift = 0.0003
    returns = np.random.normal(drift, volatility, n)
    prices = np.zeros(n)
    prices[0] = start_price
    
    for i in range(1, n):
        prices[i] = prices[i-1] * (1 + returns[i])
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': prices * (1 + np.random.normal(0, 0.005, n)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
        'volume': np.random.uniform(10e6, 100e6, n)
    })
    
    # Technicals
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['momentum_5d'] = df['close'].pct_change(5) * 100
    
    return df.dropna()

print("\n" + "="*75)
print("FINAL BACKTEST: APD with Real X Sentiment + Relaxed Thresholds")
print("="*75)

# Generate stock data
print("\nGenerating market data...")
nvda_df = generate_realistic_data(984, start_price=25, volatility=0.025)
qqq_df = generate_realistic_data(984, start_price=280, volatility=0.015)

print(f"  NVDA: {len(nvda_df)} rows")
print(f"  QQQ:  {len(qqq_df)} rows")

# Get X sentiment data (cached for no rate limits)
print("\nLoading X sentiment data...")

from fetch_x_data_eodhd import XSentimentFetcher

fetcher = XSentimentFetcher()

# Try cache first
x_data = fetcher.get_cached_mentions("NVDA")

if x_data is None or len(x_data) == 0:
    # Cache doesn't exist - fetch and cache
    print("  Cache miss - generating and caching X data...")
    x_data = fetcher.cache_x_data("NVDA", "2022-01-01", "2025-12-31")

if x_data is not None:
    print(f"  ✓ Loaded {len(x_data)} days of X data from cache")
    # Align to backtest dates
    x_data = x_data[x_data['date'].between(nvda_df['date'].min(), nvda_df['date'].max())]
else:
    print("  ⚠️  Failed to load X data")
    x_data = StockseraAPI.mock_stocksera_data("NVDA", nvda_df['close'], lead_days=2)

# Compute APD
print("\nComputing Attention-Price Divergence...")
apd_engine = APDFeatureEngine(attention_window=7, price_window=5)

# Merge data (align stock prices with X mentions)
stock_series = nvda_df[['date', 'close']].set_index('date')['close']
x_mentions = x_data[['date', 'mentions_count']].set_index('date')['mentions_count']

# Align to common dates
common_dates = stock_series.index.intersection(x_mentions.index)

if len(common_dates) < 20:
    print(f"  ⚠️  Only {len(common_dates)} matching dates")
    apd_series = pd.Series(0, index=nvda_df.index)
else:
    apd_series = apd_engine.compute_apd(x_mentions[common_dates], stock_series[common_dates])
    print(f"  ✓ APD computed ({len(apd_series)} values)")
    print(f"    Mean APD: {apd_series.mean():+.3f}")
    print(f"    Std dev: {apd_series.std():.3f}")

# Backtest
print("\nRunning backtest (Relaxed Thresholds)...")
engine = ScoringEngineAPDv2()
window = 5
results = []

# Align indices
min_len = min(len(nvda_df), len(qqq_df), len(apd_series))
nvda_aligned = nvda_df.iloc[:min_len].reset_index(drop=True)
qqq_aligned = qqq_df.iloc[:min_len].reset_index(drop=True)
apd_aligned = apd_series.iloc[:min_len].reset_index(drop=True) if len(apd_series) > 0 else pd.Series(0, index=range(min_len))

for i in range(60, min_len - window):
    hist_nvda = nvda_aligned.iloc[:i+1]
    hist_qqq = qqq_aligned.iloc[:i+1]
    apd_value = apd_aligned.iloc[i] if i < len(apd_aligned) else 0
    
    score = engine.calculate_alpha_score(hist_nvda, hist_qqq, apd_value)
    
    # Excess return
    nvda_ret = (nvda_aligned.iloc[i+window]['close'] - nvda_aligned.iloc[i]['close']) / nvda_aligned.iloc[i]['close']
    qqq_ret = (qqq_aligned.iloc[i+window]['close'] - qqq_aligned.iloc[i]['close']) / qqq_aligned.iloc[i]['close']
    excess = nvda_ret - qqq_ret
    
    correct = 0
    if score["signal"] == "BUY" and excess > 0.005:
        correct = 1
    elif score["signal"] == "SELL" and excess < -0.005:
        correct = 1
    elif score["signal"] == "HOLD" and abs(excess) < 0.02:
        correct = 1
    
    results.append({
        "signal": score["signal"],
        "alpha": score["alpha_score"],
        "apd": apd_value,
        "excess": excess,
        "correct": correct
    })

df_results = pd.DataFrame(results)

# Analysis
buy = df_results[df_results["signal"] == "BUY"]
sell = df_results[df_results["signal"] == "SELL"]
hold = df_results[df_results["signal"] == "HOLD"]

overall_acc = df_results['correct'].mean()
sharpe = (df_results['excess'].mean() / df_results['excess'].std() * np.sqrt(252)) if df_results['excess'].std() > 0 else 0

print(f"\n" + "="*75)
print(f"RESULTS")
print(f"="*75)

print(f"\nSignal Distribution:")
print(f"  Buy:  {len(buy):4d} ({len(buy)/len(df_results)*100:5.1f}%) | Accuracy: {buy['correct'].mean()*100:5.1f}%" if len(buy) > 0 else "  Buy:  0 (0.0%)")
print(f"  Hold: {len(hold):4d} ({len(hold)/len(df_results)*100:5.1f}%) | Accuracy: {hold['correct'].mean()*100:5.1f}%" if len(hold) > 0 else "  Hold: 0 (0.0%)")
print(f"  Sell: {len(sell):4d} ({len(sell)/len(df_results)*100:5.1f}%) | Accuracy: {sell['correct'].mean()*100:5.1f}%" if len(sell) > 0 else "  Sell: 0 (0.0%)")

print(f"\nPerformance Metrics:")
print(f"  Overall Accuracy: {overall_acc:.2%}")
print(f"  Avg Excess Return: {df_results['excess'].mean()*100:+.3f}%")
print(f"  Std Dev: {df_results['excess'].std()*100:.3f}%")
print(f"  Sharpe (Annualized): {sharpe:+.3f}")

print(f"\n" + "="*75)
print(f"SIGNAL EDGE TEST")
print(f"="*75)

if overall_acc > 0.52:
    print(f"✅ STRONG EDGE DETECTED")
    print(f"   Win rate: {overall_acc:.1%} (vs 50% random)")
    print(f"   Recommendation: MOVE TO OPTION 2 (Custom X Pipeline)")
elif overall_acc > 0.50:
    print(f"✓ MARGINAL EDGE")
    print(f"  Win rate: {overall_acc:.1%}")
    print(f"  Recommendation: Refine APD tuning or increase data")
else:
    print(f"✗ NO EDGE (Win rate: {overall_acc:.1%})")
    print(f"  Reason: Likely insufficient signal-to-noise")
    print(f"  Next: Inspect APD distribution, check data alignment")

print(f"="*75 + "\n")
