from strategy.base import Strategy
import pandas as pd
import numpy as np

class ContrarianVolatilitySpikeStrategy(Strategy):
    def __init__(self, symbol, vix_threshold=50, sp500_drop_threshold=0.03):
        super().__init__(symbol)
        self.vix_threshold = vix_threshold
        self.sp500_drop_threshold = sp500_drop_threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Detects extreme fear using VIX and S&P 500 crash conditions,
        and generates long signals on signs of intraday reversal.
        """
        data = data.copy()
        data['signal'] = 0

        if 'vix' not in data.columns or 'sp500' not in data.columns:
            return data

        for i in range(1, len(data)):
            vix = data['vix'].iloc[i]
            sp500_change = (data['sp500'].iloc[i] - data['sp500'].iloc[i-1]) / data['sp500'].iloc[i-1]

            # Signal 2 (Long): Extreme fear followed by intraday reversal
            if vix >= self.vix_threshold and sp500_change <= -self.sp500_drop_threshold:
                if data['close'].iloc[i] > data['open'].iloc[i]:  # Intraday reversal
                    data.loc[data.index[i], 'signal'] = 2

        return data


class MomentumScalpSmallAccountStrategy(Strategy):
    def __init__(self, symbol, momentum_window=5, threshold=0.03):
        super().__init__(symbol)
        self.momentum_window = momentum_window
        self.threshold = threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Momentum scalping strategy for small accounts:
        Looks for recent price surges with high volatility for quick long/short plays.
        """
        data = data.copy()
        data['signal'] = 0

        if len(data) < self.momentum_window:
            return data

        data['returns'] = data['close'].pct_change()
        data['momentum'] = data['close'].pct_change(periods=self.momentum_window)

        for i in range(self.momentum_window, len(data)):
            # Bullish Momentum
            if data['momentum'].iloc[i] > self.threshold and data['returns'].iloc[i] > 0:
                data.loc[data.index[i], 'signal'] = 2
            # Bearish Momentum
            elif data['momentum'].iloc[i] < -self.threshold and data['returns'].iloc[i] < 0:
                data.loc[data.index[i], 'signal'] = 1

        return data
