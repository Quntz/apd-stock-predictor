"""Scoring engine with APD as core feature"""

import pandas as pd
import numpy as np
from config import WEIGHTS
from apd_feature import APDFeatureEngine, MockAPDData

class ScoringEngineAPD:
    """
    Integrated scoring with APD (Attention-Price Divergence).
    
    Model: AlphaScore = 0.35 * Technical + 0.45 * APD + 0.20 * Sector
    
    APD is the PRIMARY alpha source (not sentiment polarity, but lead/lag).
    """
    
    def __init__(self):
        self.apd_engine = APDFeatureEngine(attention_window=7, price_window=5)
        self.weights = {
            "technical": 0.35,
            "apd": 0.45,  # Primary signal
            "sector": 0.20
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
        """Relative outperformance"""
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
        """
        Final AlphaScore with APD as primary signal.
        
        Args:
            stock_df: Stock OHLCV data
            sector_df: Sector ETF OHLCV data
            apd_value: APD value (scalar)
        
        Returns:
            dict with score breakdown
        """
        tech_score = self.score_technical(stock_df)
        apd_score = self.score_apd(apd_value)
        sector_score = self.score_sector(stock_df, sector_df)
        
        alpha_score = (
            self.weights["technical"] * tech_score +
            self.weights["apd"] * apd_score +
            self.weights["sector"] * sector_score
        )
        
        # Signal (tighter thresholds since APD is leading)
        if alpha_score > 75:
            signal = "BUY"
        elif alpha_score >= 45:
            signal = "HOLD"
        else:
            signal = "SELL"
        
        return {
            "alpha_score": round(alpha_score, 2),
            "signal": signal,
            "components": {
                "technical": round(tech_score, 2),
                "apd": round(apd_score, 2),
                "sector": round(sector_score, 2),
                "apd_raw": round(apd_value, 3)
            }
        }


if __name__ == "__main__":
    # Test APD scoring
    print("Testing APD Scoring Engine...")
    
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Create mock data
    dates = pd.date_range('2024-01-01', periods=100)
    prices = 100 + np.cumsum(np.random.normal(0.1, 1, 100))
    
    price_df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'volume': np.random.uniform(1e7, 1e8, 100)
    })
    
    # Add technicals
    delta = price_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    price_df['rsi'] = 100 - (100 / (1 + rs))
    price_df['ma20'] = price_df['close'].rolling(20).mean()
    price_df['ma60'] = price_df['close'].rolling(60).mean()
    price_df['momentum_5d'] = price_df['close'].pct_change(5) * 100
    
    price_df = price_df.dropna()
    
    # Create engine
    engine = ScoringEngineAPD()
    
    # Test scores
    print(f"\nTesting with APD values:")
    test_apds = [2.0, 1.0, 0.5, 0.0, -0.5, -1.0, -2.0]
    
    for apd_val in test_apds:
        score = engine.calculate_alpha_score(price_df, price_df, apd_val)
        print(f"  APD {apd_val:+.1f} → Score {score['alpha_score']:6.1f} | Signal: {score['signal']:6s}")
    
    print(f"\n✓ APD scoring engine working")
