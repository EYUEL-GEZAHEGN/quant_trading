import pandas as pd
import numpy as np
import pandas_ta as ta

class EMAStructureStrategy:
    def __init__(self, backcandles=15, ema_length=150, pivot_window=10, structure_backcandles=60, structure_window=11):
        self.backcandles = (backcandles)
        self.ema_length = int(ema_length)
        self.pivot_window = int(pivot_window)
        self.structure_backcandles = int(structure_backcandles)
        self.structure_window = int(structure_window)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[df['volume'] != 0].reset_index(drop=True).copy()
        df['EMA'] = ta.ema(df['close'], length=self.ema_length)

        # Compute EMASignal using vectorized approach
        highs = np.maximum(df['open'].values, df['close'].values)
        lows = np.minimum(df['open'].values, df['close'].values)
        ema = df['EMA'].values
        EMAsignal = np.zeros(len(df), dtype=int)

        for row in range(self.backcandles, len(df)):
            window_highs = highs[row - self.backcandles:row + 1]
            window_lows = lows[row - self.backcandles:row + 1]
            window_ema = ema[row - self.backcandles:row + 1]
            upt = np.all(window_lows > window_ema)
            dnt = np.all(window_highs < window_ema)
            if upt and dnt:
                EMAsignal[row] = 3
            elif upt:
                EMAsignal[row] = 2
            elif dnt:
                EMAsignal[row] = 1

        df['EMASignal'] = EMAsignal

        # Compute isPivot using rolling window for vectorization
        isPivot = np.zeros(len(df), dtype=int)
        for i in range(self.pivot_window, len(df) - self.pivot_window):
            lows = df['low'].iloc[i - self.pivot_window:i + self.pivot_window + 1]
            highs = df['high'].iloc[i - self.pivot_window:i + self.pivot_window + 1]
            center_low = df['low'].iloc[i]
            center_high = df['high'].iloc[i]

            is_low = np.all(center_low <= lows)
            is_high = np.all(center_high >= highs)

            if is_low and is_high:
                isPivot[i] = 3
            elif is_high:
                isPivot[i] = 1
            elif is_low:
                isPivot[i] = 2
        df['isPivot'] = isPivot

        df['pointpos'] = np.where(df['isPivot'] == 2, df['low'] - 1e-3,
                                   np.where(df['isPivot'] == 1, df['high'] + 1e-3, np.nan))

        # Detect structure
        pattern_detected = np.zeros(len(df), dtype=int)
        for i in range(self.structure_backcandles + self.structure_window, len(df) - self.structure_window - 1):
            localdf = df.iloc[i - self.structure_backcandles - self.structure_window:i - self.structure_window]
            highs = localdf[localdf['isPivot'] == 1]['high'].tail(3).values
            lows = localdf[localdf['isPivot'] == 2]['low'].tail(3).values
            levelbreak = 0
            zone_width = 0.001
            
            if len(lows) == 3:
                mean_low = np.mean(lows)
                if np.all(np.abs(lows - mean_low) <= zone_width) and (mean_low - df['close'].iloc[i]) > zone_width * 2:
                    levelbreak = 1

            if len(highs) == 3:
                mean_high = np.mean(highs)
                if np.all(np.abs(highs - mean_high) <= zone_width) and (df['close'].iloc[i] - mean_high) > zone_width * 2:
                    levelbreak = 2

            pattern_detected[i] = levelbreak

        df['pattern_detected'] = pattern_detected

        df['signal'] = 0
        # Add final trading signal based on conservative logic
        df['signal'] = np.where((df['EMASignal'] == 2) & (df['pattern_detected'] == 2), 2,
                        np.where((df['EMASignal'] == 1) & (df['pattern_detected'] == 1), 1, 0))


        return df
