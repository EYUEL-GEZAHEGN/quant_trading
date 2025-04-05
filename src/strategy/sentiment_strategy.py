from strategy.base import Strategy
from sentiment_fetcher import get_sentiment_score_for
import pandas as pd

class SentimentBot(Strategy):
    def __init__(self, symbol):
        self.symbol = symbol

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        score, _ = get_sentiment_score_for(self.symbol, count=50)

        signal = 0
        if score > 0.2:
            signal = 1  # Buy
        elif score < -0.2:
            signal = -1  # Sell

        data['signal'] = [signal] * len(data)
        return data
