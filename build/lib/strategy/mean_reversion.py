import pandas as pd
from strategy.base import Strategy

class MeanReversionBot(Strategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Mean Reversion Strategy:
        - Buy when z-score < -1.5
        - Sell when z-score > 1.5
        
        Signal values:
        - 2 = Bullish
        - 1 = Bearish
        - 0 = Neutral/Hold
        """
        # Calculate daily returns
        data['returns'] = data['close'].pct_change()

        # Calculate rolling mean and standard deviation
        data['mean'] = data['returns'].rolling(window=20).mean()
        data['std'] = data['returns'].rolling(window=20).std()

        # Z-score
        data['zscore'] = (data['returns'] - data['mean']) / data['std']

        # Generate signal: 2 = Bullish, 1 = Bearish, 0 = Neutral/Hold
        data['signal'] = 0  # Default to neutral/hold
        data.loc[data['zscore'] > 1.5, 'signal'] = 1  # Bearish
        data.loc[data['zscore'] < -1.5, 'signal'] = 2  # Bullish

        return data
