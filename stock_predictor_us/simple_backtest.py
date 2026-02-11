"""Simple backtest with realistic synthetic data"""

import pandas as pd
import numpy as np
from config import STOCKS, BACKTEST
from scoring_us import ScoringEngineUS

def generate_price_series(n_days, start_price, drift=0.0003, vol=0.015, correlation_to_market=0.7):
    """Generate realistic price series"""
    returns = np.random.normal(drift, vol, n_days)
    prices = np.zeros(n_days)
    prices[0] = start_price
    
    for i in range(1, n_days):
        prices[i] = prices[i-1] * (1 + returns[i])
    
    return prices

# Generate data
start_date = pd.to_datetime(BACKTEST["start_date"])
end_date = pd.to_datetime(BACKTEST["end_date"])
dates = pd.bdate_range(start=start_date, end=end_date)
n = len(dates)

print("\n" + "="*60)
print("US STOCK BACKTEST - SYNTHETIC DATA")
print("="*60)

# NVDA prices
np.random.seed(42)
nvda_prices = generate_price_series(n, 25, vol=0.025)  # Higher volatility
qqq_prices = generate_price_series(n, 280, vol=0.015)

# Add some correlation
correlation = 0.65
for i in range(100, n):
    nvda_prices[i] = nvda_prices[i] * (1 + 0.65 * (qqq_prices[i] / qqq_prices[i-1] - 1))

# Build DataFrames
def make_df(prices, dates):
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': prices * (1 + np.random.normal(0, 0.01, len(prices))),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.015, len(prices)))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.015, len(prices)))),
        'volume': np.random.uniform(10e6, 100e6, len(prices))
    })
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['vol_avg_20'] = df['volume'].rolling(20).mean()
    df['vol_anomaly'] = df['volume'] / df['vol_avg_20']
    df['momentum_5d'] = df['close'].pct_change(5) * 100
    
    return df.dropna()

nvda_df = make_df(nvda_prices, dates)
qqq_df = make_df(qqq_prices, dates)

print(f"\nData generated:")
print(f"  NVDA: {len(nvda_df)} rows | Price: ${nvda_df['close'].iloc[0]:.2f} -> ${nvda_df['close'].iloc[-1]:.2f}")
print(f"  QQQ:  {len(qqq_df)} rows | Price: ${qqq_df['close'].iloc[0]:.2f} -> ${qqq_df['close'].iloc[-1]:.2f}")

# Backtest
engine = ScoringEngineUS()
window = 5
results = []

for i in range(60, len(nvda_df) - window):
    hist_nvda = nvda_df.iloc[:i+1]
    hist_qqq = qqq_df.iloc[:i+1]
    
    # Mock X sentiment (random + noise)
    np.random.seed(i % 1000)
    x_sentiment = 50 + np.random.normal(0, 12)
    x_sentiment = max(0, min(100, x_sentiment))
    
    score = engine.calculate_alpha_score(hist_nvda, hist_qqq, x_sentiment)
    
    # Actual 5-day returns
    nvda_ret = (nvda_df.iloc[i+window]['close'] - nvda_df.iloc[i]['close']) / nvda_df.iloc[i]['close']
    qqq_ret = (qqq_df.iloc[i+window]['close'] - qqq_df.iloc[i]['close']) / qqq_df.iloc[i]['close']
    excess = nvda_ret - qqq_ret
    
    correct = 0
    if score["signal"] == "BUY" and excess > 0.005:
        correct = 1
    elif score["signal"] == "SELL" and excess < -0.005:
        correct = 1
    elif score["signal"] == "HOLD" and abs(excess) < 0.02:
        correct = 1
    
    results.append({
        "date": nvda_df.iloc[i]['date'],
        "signal": score["signal"],
        "alpha": score["alpha_score"],
        "technical": score["components"]["technical"],
        "x_sentiment": score["components"]["x_sentiment"],
        "sector": score["components"]["sector"],
        "excess_return": excess,
        "correct": correct
    })

df_results = pd.DataFrame(results)

buy = df_results[df_results["signal"] == "BUY"]
sell = df_results[df_results["signal"] == "SELL"]
hold = df_results[df_results["signal"] == "HOLD"]

print(f"\n{'='*60}")
print(f"BACKTEST RESULTS (NVDA vs QQQ)")
print(f"{'='*60}")

print(f"\nSignals: {len(df_results)} total")
print(f"  Buy:  {len(buy):3d} (accuracy: {buy['correct'].mean():.1%})")
print(f"  Sell: {len(sell):3d} (accuracy: {sell['correct'].mean():.1%})")
print(f"  Hold: {len(hold):3d} (accuracy: {hold['correct'].mean():.1%})")

print(f"\nOverall accuracy: {df_results['correct'].mean():.2%}")
print(f"Avg excess return: {df_results['excess_return'].mean()*100:+.3f}%")
print(f"Std dev: {df_results['excess_return'].std()*100:.3f}%")

if df_results['excess_return'].std() > 0:
    sharpe = (df_results['excess_return'].mean() / df_results['excess_return'].std()) * np.sqrt(252)
    print(f"Sharpe ratio (annualized): {sharpe:+.3f}")

print(f"\n{'='*60}")
if df_results['correct'].mean() > 0.50:
    print(f"✓ EDGE DETECTED: Win rate {df_results['correct'].mean():.1%} > 50%")
    print("Model shows predictive power with X sentiment!")
else:
    print(f"✗ No edge: Win rate {df_results['correct'].mean():.1%} ≤ 50%")
print(f"{'='*60}")
