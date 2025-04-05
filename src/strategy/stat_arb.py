from strategy.base import Strategy
import pandas as pd

class StatArbBot(Strategy):
    def __init__(self, symbol, pair_symbol):
        self.symbol = symbol
        self.pair_symbol = pair_symbol

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data['spread'] = data[self.symbol] - data[self.pair_symbol]
        data['mean_spread'] = data['spread'].rolling(window=20).mean()
        data['std_spread'] = data['spread'].rolling(window=20).std()

        data['zscore'] = (data['spread'] - data['mean_spread']) / data['std_spread']
        data['signal'] = 0
        data.loc[data['zscore'] > 1, 'signal'] = -1  # Short symbol, long pair
        data.loc[data['zscore'] < -1, 'signal'] = 1  # Long symbol, short pair

        return data
