import os
import json
import time
import threading
import websocket
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from alpaca.trading.client import TradingClient

# === Load Alpaca API credentials ===
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_API_SECRET_KEY")

# === Config ===
AGGREGATION_INTERVAL = 5
SYMBOLS = []
WS_URL = None

# === Shared in-memory state ===
live_bars = {}
live_quotes = {}
live_trades = {}
trade_buffer = []
buffer_lock = threading.Lock()

# === Determine Feed ===
def determine_feed(symbols):
    if all("/" in s for s in symbols):
        return "crypto", "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
    elif all("." in s for s in symbols):
        return "options", "wss://stream.data.alpaca.markets/v2/options"
    else:
        return "equity", "wss://stream.data.alpaca.markets/v2/iex"

# === WebSocket callbacks ===
def on_message(ws, message):
    global live_bars, live_quotes, live_trades

    try:
        msg = json.loads(message)

        if isinstance(msg, list):
            print("✅ Auth/Status:", msg)
            return

        if "T" not in msg:
            return

        event_type = msg["T"]
        symbol = msg.get("S")

        with buffer_lock:
            if event_type == "t":
                live_trades[symbol] = msg

            elif event_type == "q":
                live_quotes[symbol] = msg

            elif event_type == "b":
                new_bar = pd.DataFrame([{
                    "timestamp": msg["t"],
                    "open": msg.get("o"),
                    "high": msg.get("h"),
                    "low": msg.get("l"),
                    "close": msg.get("c"),
                    "volume": msg.get("v")
                }])
                if symbol not in live_bars:
                    live_bars[symbol] = new_bar
                else:
                    live_bars[symbol] = pd.concat([live_bars[symbol], new_bar]).tail(100)

    except Exception as e:
        print(f"❌ Error processing message: {e}")


def on_open(ws):
    def run():
        ws.send(json.dumps({"action": "auth", "key": API_KEY, "secret": API_SECRET}))
        ws.send(json.dumps({
            "action": "subscribe",
            "trades": SYMBOLS,
            "quotes": SYMBOLS,
            "bars": SYMBOLS
        }))
    threading.Thread(target=run).start()


def on_error(ws, error):
    print("❌ WebSocket error:", error)


def on_close(ws, status_code, msg):
    print("🔌 WebSocket closed:", msg)


def start_streaming(symbols):
    global SYMBOLS, WS_URL
    SYMBOLS = symbols
    feed_type, WS_URL = determine_feed(SYMBOLS)

    if feed_type == "equity":
        client = TradingClient(API_KEY, API_SECRET, paper=True)
        if not client.get_clock().is_open:
            print("⛔ Market is currently closed. Exiting...")
            return False

    print(f"📡 Connecting to {feed_type.upper()} WebSocket...")
    ws = websocket.WebSocketApp(WS_URL,
                                 on_open=on_open,
                                 on_message=on_message,
                                 on_error=on_error,
                                 on_close=on_close)
    threading.Thread(target=ws.run_forever, daemon=True).start()
    return True


def get_latest_bar(symbol):
    with buffer_lock:
        return live_bars.get(symbol, pd.DataFrame()).tail(1)

def get_latest_quote(symbol):
    with buffer_lock:
        return live_quotes.get(symbol, {})

def get_latest_trade(symbol):
    with buffer_lock:
        return live_trades.get(symbol, {})


if __name__ == "__main__":
    print("This script is intended to be called from main.py with dynamic symbols.")