from strategy.base import Strategy
import pandas as pd

class SentimentBot(Strategy):
    def __init__(self, symbol):
        super().__init__(symbol)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Simple sentiment-based strategy using volume and price changes
        """
        # Calculate price changes
        data['price_change'] = data['close'].pct_change()
        data['volume_change'] = data['volume'].pct_change()
        
        # Generate signals based on price and volume changes
        data['signal'] = 0
        data.loc[(data['price_change'] > 0.02) & (data['volume_change'] > 0.5), 'signal'] = 1  # Strong bullish sentiment
        data.loc[(data['price_change'] < -0.02) & (data['volume_change'] > 0.5), 'signal'] = -1  # Strong bearish sentiment
        
        return data
