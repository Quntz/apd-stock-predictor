# Real Data Workflow - Get the Truth

**Goal:** Fetch REAL X mention data + REAL prices. No synthetic data, no cheating.

---

## Setup

### 1. Clone the repo (on your machine or VPS)
```bash
git clone https://github.com/Quntz/apd-stock-predictor
cd apd-stock-predictor/stock_predictor_us
```

### 2. Install dependencies
```bash
pip install pandas numpy requests yfinance
```

### 3. Set API key
```bash
export EODHD_API_KEY="698beb4f847d90.65238585"
```

---

## Run the Pipeline

### Step 1: Fetch Real Data
```bash
python3 fetch_real_data.py
```

**What happens:**
- ✅ Fetches REAL NVIDIA X mention counts from EODHD
- ✅ Fetches REAL NVIDIA prices from Yahoo Finance
- ✅ Aligns dates (removes mismatches)
- ✅ Saves 3 files:
  - `nvda_prices_real.csv` (price data)
  - `nvda_x_mentions_real.csv` (X attention)
  - `nvda_aligned_real.csv` (merged)

**Output example:**
```
Fetching NVDA X mentions (2023-01-01 to 2026-02-11)...
  ✅ Got 750 rows from /tweets-sentiment
  Mentions avg: 523
  Date range: 2023-01-01 to 2025-11-14

Fetching NVDA prices (2023-01-01 to 2026-02-11)...
  ✅ Got 750 rows of price data
  Price range: $37.71 - $109.59

Aligned 750 matching dates
Correlation (5-day price change vs mention change): +0.234
```

### Step 2: Run Backtest
```bash
python3 backtest_real_data.py
```

**What happens:**
- Loads real aligned data
- Computes APD
- Runs 5-day prediction backtest
- Shows win rate

**Output example:**
```
BACKTEST RESULTS (Real Data)
================================

Signals: 567 total
  BUY:   45 (7.9%) | Accuracy: 62.2%
  HOLD: 480 (84.7%) | Accuracy: 28.3%
  SELL:  42 (7.4%) | Accuracy: 59.5%

Performance:
  Overall Win Rate: 45.3%
  Avg Excess Return: +0.024%
  Sharpe (Ann): +0.156

❌ NO EDGE
   Win rate: 45.3% (worse than 50% random)
   → X data doesn't predict 5-day moves
```

---

## What You'll Actually See

**Real data scenario (most likely):**

```
✓ Data fetches successfully
✓ Correlation: +0.1 to +0.3 (weak)
✓ Backtest runs
❌ Win rate: 45-52% (at or below random)
→ Conclusion: X attention doesn't predict 5-day price moves
```

**Why?**
- Stock prices follow near-random walks
- X attention is noisy and delayed
- 5-day prediction window is too short
- No real edge exists (sad but honest)

---

## If the Data Works

**Unlikely but possible scenario:**

```
✓ Correlation: > 0.4
✓ Win rate: > 55%
✓ Sharpe: > +0.5
→ Conclusion: Model actually works, proceed to production
```

**Then:**
1. Test on other stocks (TSLA, AAPL, MSFT)
2. Validate on walk-forward data (2024-2025 unseen)
3. Paper trade 2 weeks
4. Start with small real money

---

## Troubleshooting

### EODHD API fails
```
❌ All EODHD endpoints failed
```

**Solutions:**
1. Check API key: `echo $EODHD_API_KEY`
2. Verify subscription at https://stocksera.pythonanywhere.com/accounts/developers/
3. Try alternate API (Stocksera, Finnhub)

### Yahoo Finance blocked
```
❌ Price fetch failed: connection timeout
```

**Solution:**
- Use local `nvda_prices.csv` if available
- Or download manually from Yahoo Finance

### No matching dates
```
❌ No matching dates between X data and prices
   X dates: 2024-06-01 to 2025-02-11
   Price dates: 2023-01-01 to 2025-11-14
```

**Cause:**
- EODHD might only have recent X data
- Use whatever overlap exists

---

## Expected Result

**Most likely outcome:**
- ✓ Data loads and aligns
- ✓ Backtest runs
- ❌ No statistically significant edge
- → Conclusion: Dead end, move on

**Why that's OK:**
- You tested it cheaply (30 minutes)
- Now you know instead of guessing
- Can pivot to better strategy

---

## The Real Question This Answers

**"Does X attention actually predict stock prices?"**

Answer after running this: **Yes or no, with real data.**

Not "maybe" or "theoretically" — **actual numbers.**

---

## Next Steps (After You Have Numbers)

### If win_rate > 55%
```
✅ Validate on hold-out 2024 data
✅ Test on 3-5 other stocks
✅ Paper trade 2 weeks
✅ Analyze real money behavior
→ Deploy if all checks pass
```

### If win_rate < 52%
```
❌ X attention doesn't predict 5-day moves
❌ Model is likely overfitting or noise-fitting
❌ Not worth deploying
→ Archive and try different approach
```

---

## Files Generated

| File | Purpose |
|------|---------|
| `nvda_prices_real.csv` | Real NVIDIA price data |
| `nvda_x_mentions_real.csv` | Real EODHD X mention counts |
| `nvda_aligned_real.csv` | Merged data (dates matched) |
| `backtest_results_real_data.csv` | Backtest results (every signal) |

All locally saved. No cloud uploads, all private.

---

## Bottom Line

**This workflow:**
1. ✅ Gets real data (no faking)
2. ✅ Tests honestly (actual backtest)
3. ✅ Gives you the truth (yes or no)
4. ✅ Takes 10 minutes

Run it outside sandbox on your machine. Get real numbers. Then decide.
