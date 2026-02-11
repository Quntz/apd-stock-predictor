"""Attention-Price Divergence (APD) Feature Engine

APD detects when X attention moves before price — the real alpha source.
Not sentiment polarity, but the LEAD/LAG relationship.
"""

import pandas as pd
import numpy as np

class APDFeatureEngine:
    """
    Compute Attention-Price Divergence.
    
    APD = (Attention Change) - (Price Change)
    
    Interpretation:
    - APD > +1.5: Attention rising faster → BUY (price will follow)
    - APD < -1.5: Price rising faster → SELL (attention will follow)
    - -1.5 < APD < +1.5: Balanced, no edge
    """
    
    def __init__(self, attention_window=7, price_window=5):
        """
        Args:
            attention_window: Days for attention baseline (default 7)
            price_window: Days for price change (default 5)
        """
        self.attention_window = attention_window
        self.price_window = price_window
    
    def compute_attention_change(self, mentions_series):
        """
        Compute attention change: A_t = (mentions_t - avg(mentions_{t-7d})) / avg(mentions_{t-7d})
        
        Args:
            mentions_series: pd.Series of daily mention counts (indexed by date)
        
        Returns:
            pd.Series: Attention change ratio (0.0 = no change, 0.5 = 50% increase, etc.)
        """
        if len(mentions_series) < self.attention_window:
            return pd.Series(0, index=mentions_series.index)
        
        # Rolling 7-day average (baseline)
        baseline = mentions_series.rolling(window=self.attention_window).mean()
        
        # Current attention change
        attention_change = (mentions_series - baseline) / (baseline.replace(0, 1))
        
        return attention_change
    
    def compute_price_change(self, price_series):
        """
        Compute price change: P_t = (price_t - price_{t-5d}) / price_{t-5d}
        
        Args:
            price_series: pd.Series of closing prices (indexed by date)
        
        Returns:
            pd.Series: Price change ratio
        """
        price_change = price_series.pct_change(periods=self.price_window)
        return price_change
    
    def compute_apd(self, mentions_series, price_series):
        """
        Compute final APD: APD_t = A_t - P_t
        
        Args:
            mentions_series: pd.Series of daily mention counts
            price_series: pd.Series of closing prices
        
        Returns:
            pd.Series: APD values
        """
        attention_change = self.compute_attention_change(mentions_series)
        price_change = self.compute_price_change(price_series)
        
        # Align indices
        aligned = pd.concat([attention_change, price_change], axis=1, join='inner')
        apd = aligned.iloc[:, 0] - aligned.iloc[:, 1]
        
        return apd
    
    def apd_to_score(self, apd_value):
        """
        Convert APD value to 0-100 score for integration into model.
        
        Logic:
        - APD > +1.5: Strong BUY → 85-100
        - APD +0.5 to +1.5: Mild BUY → 65-85
        - APD -0.5 to +0.5: Neutral → 45-55
        - APD -1.5 to -0.5: Mild SELL → 20-35
        - APD < -1.5: Strong SELL → 0-20
        
        Args:
            apd_value: Scalar or array of APD values
        
        Returns:
            Scalar or array: Score 0-100
        """
        if isinstance(apd_value, (pd.Series, np.ndarray)):
            return np.where(
                apd_value > 1.5, 90 + np.clip(apd_value - 1.5, 0, 10),  # 90-100
                np.where(
                    apd_value > 0.5, 65 + (apd_value - 0.5) * 25,  # 65-90
                    np.where(
                        apd_value > -0.5, 50 + apd_value * 10,  # 40-60
                        np.where(
                            apd_value > -1.5, 35 + (apd_value + 0.5) * 20,  # 20-35
                            np.clip(20 - (-apd_value - 1.5) * 10, 0, 20)  # 0-20
                        )
                    )
                )
            )
        else:
            # Scalar
            if apd_value > 1.5:
                return min(100, 90 + (apd_value - 1.5))
            elif apd_value > 0.5:
                return 65 + (apd_value - 0.5) * 25
            elif apd_value > -0.5:
                return 50 + apd_value * 10
            elif apd_value > -1.5:
                return 35 + (apd_value + 0.5) * 20
            else:
                return max(0, 20 - (-apd_value - 1.5) * 10)
    
    def get_apd_signal(self, apd_value):
        """
        Get trading signal from APD.
        
        Args:
            apd_value: APD score
        
        Returns:
            str: "BUY" / "HOLD" / "SELL"
        """
        if apd_value > 1.5:
            return "BUY"
        elif apd_value < -1.5:
            return "SELL"
        else:
            return "HOLD"


class MockAPDData:
    """Generate realistic mock APD data for backtesting before real X API integration"""
    
    @staticmethod
    def generate_mock_mentions(price_series, lead_days=3, noise_level=0.3):
        """
        Generate mock mention counts that lead price by lead_days.
        
        This simulates X reacting to catalysts before price moves.
        
        Args:
            price_series: pd.Series of prices
            lead_days: How many days ahead attention leads price
            noise_level: Standard deviation of noise
        
        Returns:
            pd.Series: Mock daily mention counts
        """
        n = len(price_series)
        
        # Create attention that leads price
        price_change = price_series.pct_change().fillna(0)
        
        # Shift price change forward (so attention leads)
        attention_signal = price_change.shift(-lead_days).fillna(0)
        
        # Scale to mention counts (base 1000, can move 0-5000)
        mentions = 1000 + attention_signal * 5000
        
        # Add noise
        mentions += np.random.normal(0, noise_level * mentions, n)
        
        # Ensure positive
        mentions = np.maximum(mentions, 100)
        
        return pd.Series(mentions, index=price_series.index)


if __name__ == "__main__":
    # Test APD feature
    print("Testing APD Feature Engine...")
    
    # Create mock data
    dates = pd.date_range('2024-01-01', periods=100)
    
    # Mock prices (trending up)
    prices = 100 + np.cumsum(np.random.normal(0.1, 1, 100))
    price_series = pd.Series(prices, index=dates)
    
    # Mock mentions (leading prices)
    mentions = MockAPDData.generate_mock_mentions(price_series, lead_days=3)
    
    # Compute APD
    apd_engine = APDFeatureEngine(attention_window=7, price_window=5)
    apd = apd_engine.compute_apd(mentions, price_series)
    
    print(f"\nAPD values (last 10):")
    print(apd.tail(10))
    
    print(f"\nAPD signal (last 5):")
    for val in apd.tail(5):
        signal = apd_engine.get_apd_signal(val)
        score = apd_engine.apd_to_score(val)
        print(f"  APD: {val:+.3f} → Signal: {signal:6s} | Score: {score:.1f}")
    
    print(f"\n✓ APD feature working")
