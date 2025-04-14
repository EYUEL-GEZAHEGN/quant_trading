import pandas as pd
import pyarrow.parquet as pq

df_quotes = pq.read_table("data/quotes/ETH_USD").to_pandas()
df_bars = pq.read_table("data/bars/BTC_USD").to_pandas()

print(df_quotes)
print(df_bars.tail)
