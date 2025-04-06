from strategy.base import Strategy
import pandas as pd
import numpy as np

class StatArbBot(Strategy):
    def __init__(self, symbol, pair_symbol):
        super().__init__(symbol)
        self.pair_symbol = pair_symbol

    def generate_signals(self, data: tuple) -> pd.DataFrame:
        """
        Statistical Arbitrage Strategy:
        - Calculate spread between two assets
        - Trade when spread deviates significantly from mean
        """
        df1, df2 = data
        spread = df1['close'] - df2['close']
        
        # Calculate z-score of spread
        spread_mean = spread.rolling(window=20).mean()
        spread_std = spread.rolling(window=20).std()
        zscore = (spread - spread_mean) / spread_std
        
        # Generate signals
        df1['signal'] = 0
        df1.loc[zscore > 2, 'signal'] = -1  # Sell when spread is too high
        df1.loc[zscore < -2, 'signal'] = 1  # Buy when spread is too low
        
        return df1
