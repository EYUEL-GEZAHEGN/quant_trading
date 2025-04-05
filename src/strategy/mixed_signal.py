import pandas as pd
from strategy.ta_strategy import TAIndicatorStrategy
from strategy.mean_reversion import MeanReversionBot
# Add more strategies as needed

class MixedSignalsStrategy:
    def __init__(self, symbol):
        self.symbol = symbol
        self.ta_strategy = TAIndicatorStrategy(symbol)
        self.mean_reversion = MeanReversionBot(symbol)
        # Add other strategy instances here

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        # Get signals from each strategy
        ta_signals = self.ta_strategy.generate_signals(df)
        mr_signals = self.mean_reversion.generate_signals(df)

        # Align signals to same index
        ta_signals = ta_signals[['signal']].rename(columns={'signal': 'ta_signal'})
        mr_signals = mr_signals[['signal']].rename(columns={'signal': 'mr_signal'})

        df = df.join(ta_signals)
        df = df.join(mr_signals)

        # === Combine logic ===
        # Majority voting: only signal if both agree
        df['signal'] = 0
        df.loc[(df['ta_signal'] == 1) & (df['mr_signal'] == 1), 'signal'] = 1
        df.loc[(df['ta_signal'] == -1) & (df['mr_signal'] == -1), 'signal'] = -1

        return df
