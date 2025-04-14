import websocket
import json
import threading
import os

from dotenv import load_dotenv
from datetime import datetime

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_API_SECRET_KEY")
BASE_URL = "wss://paper-api.alpaca.markets/stream"  # For paper trading

import websocket
import json
import threading
from datetime import datetime
import csv


# CSV file path to log updates (optional)
CSV_FILE = "trade_updates_log.csv"

# Create CSV header if the file doesn't exist
def initialize_csv():
    try:
        with open(CSV_FILE, 'x', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "event", "symbol", "order_id", "status", "filled_qty", "avg_price", "side"])
    except FileExistsError:
        pass

# Handle incoming messages
def on_message(ws, message):
    try:
        data = json.loads(message)
        stream = data.get("stream", "")
        if stream == "trade_updates":
            update = data.get("data", {})
            order = update.get("order", {})
            event_type = update.get("event", "N/A")
            order_id = order.get("id", "")
            symbol = order.get("symbol", "")
            status = order.get("status", "")
            filled_qty = order.get("filled_qty", "0")
            avg_price = order.get("filled_avg_price", "0")
            side = order.get("side", "")
            time = update.get("timestamp", datetime.utcnow().isoformat())

            # 🌐 Structured Console Output
            print(f"\n📦 TRADE UPDATE [{event_type.upper()}]")
            print(f"📍 Symbol     : {symbol}")
            print(f"🆔 Order ID   : {order_id}")
            print(f"📊 Status     : {status}")
            print(f"📈 Qty Filled : {filled_qty}")
            print(f"💵 Avg Price  : {avg_price}")
            print(f"📥 Side       : {side}")
            print(f"⏱ Timestamp  : {time}")

            # 📝 Save to CSV
            with open(CSV_FILE, mode="a", newline='') as file:
                writer = csv.writer(file)
                writer.writerow([time, event_type, symbol, order_id, status, filled_qty, avg_price, side])
        else:
            print("📥 Raw Message:", data)
    except Exception as e:
        print("⚠️ Error parsing message:", e)

# Handle WebSocket errors
def on_error(ws, error):
    print("❌ Error:", error)

# Handle WebSocket close
def on_close(ws, close_status_code, close_msg):
    print("🔌 Disconnected:", close_msg)

# Authenticate and subscribe
def on_open(ws):
    print("✅ Connected. Authenticating...")

    # ✅ NEW FORMAT (2025-compliant)
    auth_msg = {
        "action": "auth",
        "key": API_KEY,
        "secret": API_SECRET
    }
    ws.send(json.dumps(auth_msg))

    def subscribe():
        import time
        time.sleep(1)
        listen_msg = {
            "action": "listen",
            "data": {
                "streams": ["trade_updates"]
            }
        }
        ws.send(json.dumps(listen_msg))

    threading.Thread(target=subscribe).start()

# Initialize logging file
initialize_csv()

# Connect to Alpaca WebSocket
ws = websocket.WebSocketApp(BASE_URL,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

print("📡 Starting Alpaca Trade Update Stream...")
ws.run_forever()

