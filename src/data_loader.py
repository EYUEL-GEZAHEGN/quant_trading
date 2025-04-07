from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from config import settings
import pandas as pd
import os
from datetime import datetime

client = StockHistoricalDataClient(settings.ALPACA_API_KEY_ID, settings.ALPACA_API_SECRET_KEY)

def load_data(symbol: str, start_date: str, end_date: str, timeframe: str = "1Min") -> pd.DataFrame:
    cache_dir = f"data/cache"
    os.makedirs(cache_dir, exist_ok=True)

    file_name = f"{symbol}_{start_date}_{end_date}_{timeframe}.csv".replace(":", "-")
    file_path = os.path.join(cache_dir, file_name)

    if os.path.exists(file_path):
        print(f"📦 Loading cached data from {file_path}")
        df = pd.read_csv(file_path, index_col="timestamp", parse_dates=True)
        return df

    print(f"🔄 Fetching fresh data from Alpaca for {symbol} ({start_date} to {end_date})")

    # ✅ Convert date strings to datetime objects
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=start_dt,
        end=end_dt
    )

    bars = client.get_stock_bars(request).df

# If only one symbol is returned, 'symbol' column won't exist
    if 'symbol' in bars.columns:
        bars = bars[bars['symbol'] == symbol].copy()
    else:
        bars = bars.copy()

    # Flatten MultiIndex if necessary
    if isinstance(bars.index, pd.MultiIndex):
        bars.reset_index(inplace=True)
        bars.set_index("timestamp", inplace=True)

    bars.rename(columns={'close': 'close'}, inplace=True)


    bars.to_csv(file_path)
    print(f"✅ Cached data to {file_path}")

    return bars

def load_pair_data(symbol1: str, symbol2: str, start_date: str, end_date: str) -> pd.DataFrame:
    df1 = load_data(symbol1, start_date, end_date)
    df2 = load_data(symbol2, start_date, end_date)

    df = pd.DataFrame(index=df1.index)
    df[symbol1] = df1['close']
    df[symbol2] = df2['close']
    return df