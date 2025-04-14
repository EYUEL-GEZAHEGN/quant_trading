
"""
import websocket
import json
import threading
import pandas as pd
from datetime import datetime
import os

import os

from dotenv import load_dotenv
from datetime import datetime

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_API_SECRET_KEY")
BASE_URL = "wss://paper-api.alpaca.markets/stream"  # For paper trading
FEED = 'iex'  # or 'sip' for premium
WS_URL = f"wss://stream.data.alpaca.markets/v2/{FEED}"

# === DataFrames for live tracking ===
trade_data = []
quote_data = []
bar_data = []

def on_message(ws, message):
    global trade_data, quote_data, bar_data

    msg = json.loads(message)
    if isinstance(msg, list):  # auth success etc.
        print("✅ Auth/Status:", msg)
        return

    data = msg
    event_type = data.get("T")

    if event_type == "t":  # Trade
        trade_data.append({
            "Type": "Trade",
            "Symbol": data["S"],
            "Price": data["p"],
            "Size": data["s"],
            "Exchange": data["x"],
            "Timestamp": data["t"]
        })

    elif event_type == "q":  # Quote
        quote_data.append({
            "Type": "Quote",
            "Symbol": data["S"],
            "Bid": data["bp"],
            "Ask": data["ap"],
            "BidSize": data["bs"],
            "AskSize": data["as"],
            "Timestamp": data["t"]
        })

    elif event_type == "b":  # Bar
        bar_data.append({
            "Type": "Bar",
            "Symbol": data["S"],
            "Open": data["o"],
            "High": data["h"],
            "Low": data["l"],
            "Close": data["c"],
            "Volume": data["v"],
            "Timestamp": data["t"]
        })

    os.system('cls' if os.name == 'nt' else 'clear')  # Clear terminal for refresh
    print("📈 Latest Trades")
    print(pd.DataFrame(trade_data[-5:]))  # Show last 5 trades
    print("\n💬 Latest Quotes")
    print(pd.DataFrame(quote_data[-5:]))
    print("\n📊 Latest Bars")
    print(pd.DataFrame(bar_data[-5:]))

def on_error(ws, error):
    print("❌ Error:", error)

def on_close(ws, code, msg):
    print("🔌 Closed:", msg)

def on_open(ws):
    def run():
        ws.send(json.dumps({
            "action": "auth",
            "key": API_KEY,
            "secret": API_SECRET
        }))
        ws.send(json.dumps({
            "action": "subscribe",
            "trades": ["AAPL", "QQQ"],
            "quotes": ["AAPL", "QQQ"],
            "bars": ["AAPL", "QQQ"]
        }))
    threading.Thread(target=run).start()

# === Connect to Alpaca WebSocket ===
ws = websocket.WebSocketApp(WS_URL,
                             on_open=on_open,
                             on_message=on_message,
                             on_error=on_error,
                             on_close=on_close)

print("📡 Connecting to Alpaca Market Data...")
ws.run_forever()
"""


import os
from dotenv import load_dotenv
from datetime import datetime
import websocket
import json
import threading
import time
from datetime import datetime
import pandas as pd

# Your Alpaca credentials
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_API_SECRET_KEY")
WS_URL = 'wss://stream.data.alpaca.markets/v2/iex'

# Global trade buffer for aggregation
trade_buffer = []

# Interval for custom bars (in seconds)
AGGREGATION_INTERVAL = 5

def on_message(ws, message):
    global trade_buffer
    msg = json.loads(message)

    if isinstance(msg, list):  # Auth success
        print("✅ Auth/Status:", msg)
        return

    if msg.get("T") == "t":  # Trade message
        trade_buffer.append({
            "timestamp": pd.to_datetime(msg["t"]),
            "symbol": msg["S"],
            "price": msg["p"],
            "size": msg["s"]
        })

def aggregate_trades():
    global trade_buffer
    while True:
        time.sleep(AGGREGATION_INTERVAL)
        if trade_buffer:
            df = pd.DataFrame(trade_buffer)
            df.set_index("timestamp", inplace=True)

            # Resample and aggregate into OHLCV
            grouped = df.groupby("symbol").resample(f"{AGGREGATION_INTERVAL}s").agg({
                "price": ["first", "max", "min", "last"],
                "size": "sum"
            }).dropna()

            if not grouped.empty:
                grouped.columns = ["Open", "High", "Low", "Close", "Volume"]
                print(f"\n🕒 {datetime.utcnow().strftime('%H:%M:%S')} - {AGGREGATION_INTERVAL}s OHLCV")
                print(grouped)

            # Clear processed buffer
            trade_buffer = []

def on_error(ws, error):
    print("❌", error)

def on_close(ws, close_status_code, close_msg):
    print("🔌 Closed")

def on_open(ws):
    def run():
        ws.send(json.dumps({
            "action": "auth",
            "key": API_KEY,
            "secret": API_SECRET
        }))
        ws.send(json.dumps({
            "action": "subscribe",
            "trades": ["AAPL"]
        }))
    threading.Thread(target=run).start()

# Run WebSocket and aggregation in parallel
def start_streaming():
    agg_thread = threading.Thread(target=aggregate_trades)
    agg_thread.daemon = True
    agg_thread.start()

    ws = websocket.WebSocketApp(WS_URL,
                                 on_open=on_open,
                                 on_message=on_message,
                                 on_error=on_error,
                                 on_close=on_close)
    ws.run_forever()

start_streaming()
