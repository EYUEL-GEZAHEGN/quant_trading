from strategy.base import Strategy
import pandas as pd
import numpy as np

class TAIndicatorStrategy(Strategy):
    def __init__(self, symbol):
        super().__init__(symbol)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Technical Analysis Strategy using multiple indicators:
        - RSI
        - MACD
        - Bollinger Bands
        
        Signal values:
        - 2 = Bullish
        - 1 = Bearish
        - 0 = Neutral/Hold
        """
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = data['close'].ewm(span=12, adjust=False).mean()
        exp2 = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = exp1 - exp2
        data['signal_line'] = data['macd'].ewm(span=9, adjust=False).mean()
        
        # Calculate Bollinger Bands
        data['bb_middle'] = data['close'].rolling(window=20).mean()
        data['bb_std'] = data['close'].rolling(window=20).std()
        data['bb_upper'] = data['bb_middle'] + (data['bb_std'] * 2)
        data['bb_lower'] = data['bb_middle'] - (data['bb_std'] * 2)
        
        # Generate signals
        data['signal'] = 0  # Default to neutral/hold
        
        # RSI signals
        data.loc[data['rsi'] < 30, 'signal'] = 2  # Oversold = Bullish
        data.loc[data['rsi'] > 70, 'signal'] = 1  # Overbought = Bearish
        
        # MACD signals
        data.loc[data['macd'] > data['signal_line'], 'signal'] = 2  # Bullish crossover
        data.loc[data['macd'] < data['signal_line'], 'signal'] = 1  # Bearish crossover
        
        # Bollinger Band signals
        data.loc[data['close'] < data['bb_lower'], 'signal'] = 2  # Price below lower band
        data.loc[data['close'] > data['bb_upper'], 'signal'] = 1  # Price above upper band
        
        # If multiple indicators conflict, use the majority
        bullish_count = ((data['rsi'] < 30).astype(int) + 
                         (data['macd'] > data['signal_line']).astype(int) + 
                         (data['close'] < data['bb_lower']).astype(int))
        
        bearish_count = ((data['rsi'] > 70).astype(int) + 
                         (data['macd'] < data['signal_line']).astype(int) + 
                         (data['close'] > data['bb_upper']).astype(int))
        
        data.loc[bullish_count > bearish_count, 'signal'] = 2  # Bullish
        data.loc[bearish_count > bullish_count, 'signal'] = 1  # Bearish
        data.loc[bullish_count == bearish_count, 'signal'] = 0  # Neutral/Hold
        
        return data

#python main.py --mode backtest --strategy ta_indicator --symbol TQQQ --start 2025-03-07 --end 2025-03-28