from strategy.base import Strategy
import pandas as pd
import numpy as np

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

#python main.py --mode backtest --strategy harris_candles --symbol TQQQ --start 2025-03-07 --end 2025-03-28
