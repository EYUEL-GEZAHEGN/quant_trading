import pandas as pd
from strategy.base import Strategy

class MeanReversionBot(Strategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Mean Reversion Strategy:
        - Buy when z-score < -1.5
        - Sell when z-score > 1.5
        """
        # Calculate daily returns
        data['returns'] = data['close'].pct_change()

        # Calculate rolling mean and standard deviation
        data['mean'] = data['returns'].rolling(window=20).mean()
        data['std'] = data['returns'].rolling(window=20).std()

        # Z-score
        data['zscore'] = (data['returns'] - data['mean']) / data['std']

        # Generate signal: 1 = Buy, -1 = Sell, 0 = Hold
        data['signal'] = 0
        data.loc[data['zscore'] > 1.5, 'signal'] = -1
        data.loc[data['zscore'] < 1.5, 'signal'] = 1

        return data
