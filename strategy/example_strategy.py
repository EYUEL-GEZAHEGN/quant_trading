class ExampleStrategy:
    def get_target_symbols(self):
        return ["AAPL"]

    def generate_signal(self, symbol, bar_df):
        close = bar_df["Close"].values[-1]
        open_ = bar_df["Open"].values[-1]

        if close > open_ * 1.01:
            return "BUY"
        elif close < open_ * 0.99:
            return "SELL"
        return "HOLD"
