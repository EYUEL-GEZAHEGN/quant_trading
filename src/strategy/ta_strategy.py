import pandas as pd
from strategy.base import Strategy
import ta

class TAIndicatorStrategy(Strategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        # === RSI ===
        df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()

        # === EMA ===
        df['ema_20'] = ta.trend.EMAIndicator(close=df['close'], window=20).ema_indicator()
        df['ema_50'] = ta.trend.EMAIndicator(close=df['close'], window=50).ema_indicator()

        # === Pivot Point + Support/Resistance ===
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['s1'] = (2 * df['pivot']) - df['high']
        df['s2'] = df['pivot'] - (df['high'] - df['low'])
        df['r1'] = (2 * df['pivot']) - df['low']
        df['r2'] = df['pivot'] + (df['high'] - df['low'])

        df.dropna(inplace=True)

        # === Signal Logic ===
        
        #df['signal'] = 0
        #df.loc[df['rsi'] < 40, 'signal'] = 1
        #df.loc[df['rsi'] > 60, 'signal'] = -1

        df['signal'] = 0
        df.loc[(df['rsi'] < 33) & (df['close'] > df['ema_20']), 'signal'] = 1
        df.loc[(df['rsi'] > 67) & (df['close'] < df['ema_20']), 'signal'] = -1
        
        return df
    
        #df['signal'] = 1  # ⬅️ Force buy every time
        #return df
    
#python main.py --mode backtest --strategy ta_indicator --symbol TQQQ --start 2025-03-07 --end 2025-03-28