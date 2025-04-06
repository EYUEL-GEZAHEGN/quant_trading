from strategy.base import Strategy
import pandas as pd
import numpy as np

class MixedSignalsStrategy(Strategy):
    def __init__(self, symbol):
        super().__init__(symbol)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Mixed Signals Strategy combining multiple indicators:
        - Moving Average Crossovers
        - RSI
        - Volume Analysis
        - Price Momentum
        
        Signal values:
        - 2 = Bullish
        - 1 = Bearish
        - 0 = Neutral/Hold
        """
        # Calculate moving averages
        data['sma_20'] = data['close'].rolling(window=20).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate volume indicators
        data['volume_sma'] = data['volume'].rolling(window=20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        # Calculate momentum
        data['momentum'] = data['close'].pct_change(periods=10)
        
        # Initialize signal column
        data['signal'] = 0  # Default to neutral/hold
        
        # Calculate bullish and bearish counts
        bullish_count = (
            (data['sma_20'] > data['sma_50']).astype(int) +
            (data['rsi'] < 30).astype(int) +
            (data['volume_ratio'] > 2).astype(int) +
            (data['momentum'] > 0.05).astype(int)
        )
        
        bearish_count = (
            (data['sma_20'] < data['sma_50']).astype(int) +
            (data['rsi'] > 70).astype(int) +
            (data['volume_ratio'] < 0.5).astype(int) +
            (data['momentum'] < -0.05).astype(int)
        )
        
        # Set signals based on majority
        data.loc[bullish_count > bearish_count, 'signal'] = 2  # Bullish
        data.loc[bearish_count > bullish_count, 'signal'] = 1  # Bearish
        data.loc[bullish_count == bearish_count, 'signal'] = 0  # Neutral/Hold
        
        return data
