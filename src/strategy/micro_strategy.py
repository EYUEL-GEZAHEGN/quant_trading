from strategy.base import Strategy
import pandas as pd
import numpy as np

class MicroMomentum(Strategy):
    def __init__(self, symbol):
        super().__init__(symbol)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        data['signal'] = 0

        if len(data) < 15:
            return data

        # Calculate indicators
        data['sma_5'] = data['close'].rolling(window=5).mean()
        data['ema_5'] = data['close'].ewm(span=5).mean()
        data['vwap'] = (data['close'] * data['volume']).cumsum() / data['volume'].cumsum()
        data['rsi'] = self.rsi(data['close'])

        # Bullish condition → 2
        bullish_condition = (
            (data['close'] > data['sma_5']) &
            (data['close'] > data['ema_5']) &
            (data['close'] > data['vwap']) &
            (data['rsi'] < 40)
        )
        data.loc[bullish_condition, 'signal'] = 2

        # Bearish condition → 1
        bearish_condition = (
            (data['close'] < data['sma_5']) &
            (data['close'] < data['ema_5']) &
            (data['close'] < data['vwap']) &
            (data['rsi'] > 60)
        )
        data.loc[bearish_condition, 'signal'] = 1

        # Else → stays 0 (neutral)
        return data

    def rsi(self, prices, period=14):
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
