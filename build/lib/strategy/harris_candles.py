from strategy.base import Strategy
import pandas as pd
import numpy as np

"BACKTEST SHOWS THAT THIS STRATEGY PERMOED WELL ON THE SPY BY GIVING A GOOD RISK ADJUSTED RETURN, AND AMAZING ALPHA,BUT IT TOOK ONLY 5 TRADES IN 371 DAYS "

class HarrisCandlesStrategy(Strategy):
    def __init__(self, symbol):
        super().__init__(symbol)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:

        """
        Harris Systematic Candlestick Pattern Strategy:
        - Looks for specific 5-candle patterns
        - Signal 2 (Bullish): Series of higher lows followed by breakout
        - Signal 1 (Bearish): Series of lower highs followed by breakdown
        """

        # Initialize signal column
        data['signal'] = 0
        
        # Need at least 5 candles for the pattern
        if len(data) < 5:
            return data
            
        # Calculate signals for each candle
        for i in range(4, len(data)):
            # Bullish Pattern (Signal 2)
            c1 = data['low'].iloc[i-4] > data['high'].iloc[i]
            c2 = data['high'].iloc[i] > data['low'].iloc[i-3]
            c3 = data['low'].iloc[i-3] > data['low'].iloc[i-2]
            c4 = data['low'].iloc[i-2] > data['low'].iloc[i-1]
            c5 = data['close'].iloc[i] > data['high'].iloc[i-1]
            
            if c1 and c2 and c3 and c4 and c5:
                data.loc[data.index[i], 'signal'] = 2
                continue
                
            # Bearish Pattern (Signal 1)
            c1 = data['high'].iloc[i-4] < data['low'].iloc[i]
            c2 = data['low'].iloc[i] < data['high'].iloc[i-3]
            c3 = data['high'].iloc[i-3] < data['high'].iloc[i-2]
            c4 = data['high'].iloc[i-2] < data['high'].iloc[i-1]
            c5 = data['close'].iloc[i] < data['low'].iloc[i-1]
            
            if c1 and c2 and c3 and c4 and c5:
                data.loc[data.index[i], 'signal'] = 1
        
        return data

        

"""
from strategy.base import Strategy
import pandas as pd


QUICK TRADING VERSION OF HARRIS CANDLES STRATEGY:
- Adjusted to be more responsive and catch quicker reversals.
- Backtest shows conservative trades with high alpha but low frequency.
- This version enables faster trade cycles.


class HarrisCandlesStrategy(Strategy):
    def __init__(self, symbol, pattern_window=3):
        super().__init__(symbol)
        self.pattern_window = pattern_window  # smaller window means faster trades

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['signal'] = 0

        if len(data) < self.pattern_window + 2:
            return data

        for i in range(self.pattern_window + 1, len(data)):
            lows = data['low'].iloc[i - self.pattern_window:i]
            highs = data['high'].iloc[i - self.pattern_window:i]

            # Bullish Quick Pattern
            bullish = all(lows[j] > lows[j+1] for j in range(len(lows)-1)) and \
                      data['close'].iloc[i] > highs.iloc[-1]

            # Bearish Quick Pattern
            bearish = all(highs[j] < highs[j+1] for j in range(len(highs)-1)) and \
                      data['close'].iloc[i] < lows.iloc[-1]

            if bullish:
                data.loc[data.index[i], 'signal'] = 2
            elif bearish:
                data.loc[data.index[i], 'signal'] = 1

        return data
"""
