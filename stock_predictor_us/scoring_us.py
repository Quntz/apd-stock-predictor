"""Scoring engine: Technical + X Sentiment + Sector"""

import pandas as pd
import numpy as np
from config import WEIGHTS

class ScoringEngineUS:
    def __init__(self):
        self.weights = WEIGHTS
    
    def score_technical(self, df):
        """Technical score: RSI + Trend + Momentum"""
        if df.empty or len(df) < 60:
            return 50
        
        latest = df.iloc[-1]
        
        # RSI (oversold = bullish, overbought = bearish)
        rsi = latest['rsi']
        if pd.isna(rsi):
            rsi_score = 50
        elif rsi < 30:
            rsi_score = 80
        elif rsi > 70:
            rsi_score = 20
        else:
            rsi_score = 20 + (rsi - 30) * 0.8
        
        # Trend (MA20 > MA60 = bullish)
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
        
        # Momentum (5-day change)
        momentum = latest['momentum_5d']
        if pd.notna(momentum):
            momentum_score = 50 + momentum * 5  # Scale
            momentum_score = max(0, min(100, momentum_score))
        else:
            momentum_score = 50
        
        # Weighted
        tech_score = 0.45 * rsi_score + 0.35 * trend_score + 0.20 * momentum_score
        return max(0, min(100, tech_score))
    
    def score_x_sentiment(self, x_sentiment_score):
        """X sentiment score (0-100)"""
        return max(0, min(100, x_sentiment_score))
    
    def score_sector(self, stock_df, sector_df):
        """Relative outperformance vs sector ETF"""
        if stock_df.empty or sector_df.empty or len(stock_df) < 20:
            return 50
        
        # 5-day relative performance
        if len(stock_df) >= 5 and len(sector_df) >= 5:
            stock_return = (stock_df.iloc[-1]['close'] - stock_df.iloc[-6]['close']) / stock_df.iloc[-6]['close']
            sector_return = (sector_df.iloc[-1]['close'] - sector_df.iloc[-6]['close']) / sector_df.iloc[-6]['close']
            relative = stock_return - sector_return
        else:
            relative = 0
        
        sector_score = 50 + (relative * 250)  # Scale
        return max(0, min(100, sector_score))
    
    def calculate_alpha_score(self, stock_df, sector_df, x_sentiment):
        """Final AlphaScore"""
        tech_score = self.score_technical(stock_df)
        sentiment_score = self.score_x_sentiment(x_sentiment)
        sector_score = self.score_sector(stock_df, sector_df)
        
        alpha_score = (
            self.weights["technical"] * tech_score +
            self.weights["x_sentiment"] * sentiment_score +
            self.weights["sector"] * sector_score
        )
        
        # Signal
        if alpha_score > 75:
            signal = "BUY"
        elif alpha_score >= 50:
            signal = "HOLD"
        else:
            signal = "SELL"
        
        return {
            "alpha_score": round(alpha_score, 2),
            "signal": signal,
            "components": {
                "technical": round(tech_score, 2),
                "x_sentiment": round(sentiment_score, 2),
                "sector": round(sector_score, 2)
            }
        }
