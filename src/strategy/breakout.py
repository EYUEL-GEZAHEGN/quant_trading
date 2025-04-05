from strategy.base import Strategy
import pandas as pd

class BreakoutBot(Strategy):
    def __init__(self, symbol):
        self.symbol = symbol

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data['signal'] = 0

        # Simple 20-period breakout logic
        data['high_20'] = data['high'].rolling(window=20).max()
        data['low_20'] = data['low'].rolling(window=20).min()

        data['signal'] = 0
        data.loc[data['close'] > data['high_20'], 'signal'] = 1   # Breakout long
        data.loc[data['close'] < data['low_20'], 'signal'] = -1  # Breakdown short

        return data
