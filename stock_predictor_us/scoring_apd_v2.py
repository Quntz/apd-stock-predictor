"""Scoring Engine v2: APD with Relaxed Thresholds + Real Stocksera Data"""

import pandas as pd
import numpy as np
from apd_feature import APDFeatureEngine

class ScoringEngineAPDv2:
    """
    Updated model with:
    - Relaxed BUY/SELL thresholds (avoid zero-signal bias)
    - Better threshold distribution (33/33/33 signal split)
    - Weights tuned for real X data
    """
    
    def __init__(self):
        self.apd_engine = APDFeatureEngine(attention_window=7, price_window=5)
        self.weights = {
            "technical": 0.35,
            "apd": 0.45,
            "sector": 0.20
        }
        
        # RELAXED thresholds (avoid zero-signal bias)
        # Target: ~33% BUY, 33% HOLD, 33% SELL signals
        self.signals = {
            "buy": 60,      # Was 75 (too tight)
            "sell": 40      # Was 45 (was sell threshold)
        }
    
    def score_technical(self, df):
        """Technical score: RSI + Trend + Momentum"""
        if df.empty or len(df) < 60:
            return 50
        
        latest = df.iloc[-1]
        
        # RSI
        rsi = latest['rsi']
        if pd.isna(rsi):
            rsi_score = 50
        elif rsi < 30:
            rsi_score = 80
        elif rsi > 70:
            rsi_score = 20
        else:
            rsi_score = 20 + (rsi - 30) * 0.8
        
        # Trend (MA20 vs MA60)
        ma20 = latest['ma20']
        ma60 = latest['ma60']
        
        if pd.notna(ma20) and pd.notna(ma60):
            if ma20 > ma60 * 1.02:
                trend_score = 80
            elif ma20 > ma60:
                trend_score = 60
            elif ma20 < ma60 * 0.98:
                trend_score = 20
            else:
                trend_score = 40
        else:
            trend_score = 50
        
        # Momentum
        momentum = latest['momentum_5d']
        if pd.notna(momentum):
            momentum_score = 50 + momentum * 5
            momentum_score = max(0, min(100, momentum_score))
        else:
            momentum_score = 50
        
        tech_score = 0.45 * rsi_score + 0.35 * trend_score + 0.20 * momentum_score
        return max(0, min(100, tech_score))
    
    def score_apd(self, apd_value):
        """Convert APD to 0-100 score"""
        return self.apd_engine.apd_to_score(apd_value)
    
    def score_sector(self, stock_df, sector_df):
        """Relative outperformance vs sector baseline"""
        if stock_df.empty or sector_df.empty or len(stock_df) < 20:
            return 50
        
        if len(stock_df) >= 5 and len(sector_df) >= 5:
            stock_ret = (stock_df.iloc[-1]['close'] - stock_df.iloc[-6]['close']) / stock_df.iloc[-6]['close']
            sector_ret = (sector_df.iloc[-1]['close'] - sector_df.iloc[-6]['close']) / sector_df.iloc[-6]['close']
            relative = stock_ret - sector_ret
        else:
            relative = 0
        
        sector_score = 50 + (relative * 250)
        return max(0, min(100, sector_score))
    
    def calculate_alpha_score(self, stock_df, sector_df, apd_value):
        """Calculate AlphaScore with relaxed thresholds"""
        tech_score = self.score_technical(stock_df)
        apd_score = self.score_apd(apd_value)
        sector_score = self.score_sector(stock_df, sector_df)
        
        alpha_score = (
            self.weights["technical"] * tech_score +
            self.weights["apd"] * apd_score +
            self.weights["sector"] * sector_score
        )
        
        # Signal (RELAXED thresholds)
        if alpha_score > self.signals["buy"]:
            signal = "BUY"
        elif alpha_score < self.signals["sell"]:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        return {
            "alpha_score": round(alpha_score, 2),
            "signal": signal,
            "components": {
                "technical": round(tech_score, 2),
                "apd": round(apd_score, 2),
                "sector": round(sector_score, 2)
            }
        }


if __name__ == "__main__":
    print("Testing APD Scoring Engine v2 (Relaxed Thresholds)...")
    
    import pandas as pd
    import numpy as np
    
    # Mock data
    dates = pd.date_range('2024-01-01', periods=100)
    prices = 100 + np.cumsum(np.random.normal(0.1, 1, 100))
    
    price_df = pd.DataFrame({
        'close': prices,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'volume': np.random.uniform(1e7, 1e8, 100)
    })
    
    delta = price_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    price_df['rsi'] = 100 - (100 / (1 + rs))
    price_df['ma20'] = price_df['close'].rolling(20).mean()
    price_df['ma60'] = price_df['close'].rolling(60).mean()
    price_df['momentum_5d'] = price_df['close'].pct_change(5) * 100
    price_df = price_df.dropna()
    
    engine = ScoringEngineAPDv2()
    
    # Test signal distribution
    signals = {"BUY": 0, "HOLD": 0, "SELL": 0}
    
    for apd_val in np.linspace(-2, 2, 21):
        score = engine.calculate_alpha_score(price_df, price_df, apd_val)
        signals[score["signal"]] += 1
        
    total = sum(signals.values())
    print(f"\nSignal Distribution (target: ~33% each):")
    print(f"  BUY:  {signals['BUY']:3d} ({signals['BUY']/total*100:5.1f}%)")
    print(f"  HOLD: {signals['HOLD']:3d} ({signals['HOLD']/total*100:5.1f}%)")
    print(f"  SELL: {signals['SELL']:3d} ({signals['SELL']/total*100:5.1f}%)")
    
    print(f"\n✓ Thresholds relaxed - should see more balanced signal distribution")
