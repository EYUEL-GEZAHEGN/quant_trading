import pandas as pd

class CryptoMomentumStrategy:
    def get_target_symbols(self):
        return ["SOL/USDT"]

    def generate_signal(self, symbol, bar_df: pd.DataFrame) -> str:
        if bar_df.empty:
            print(f"⚠️ No data for {symbol}")
            return "HOLD"

        latest = bar_df.iloc[-1]
        if latest["close"] == latest["close"]:  # always true
            print(f"✅ Condition met for {symbol}: close == close → BUY")
            return "BUY"

        return "HOLD"
