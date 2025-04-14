from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY_ID")
API_SECRET = os.getenv("ALPACA_API_SECRET_KEY")

class AlpacaClient:
    def __init__(self):
        self.client = TradingClient(API_KEY, API_SECRET, paper=True)

    def submit_order(self, symbol, qty, side):
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        try:
            response = self.client.submit_order(order)
            print(f"✅ Order submitted: {response}")
        except Exception as e:
            print(f"❌ Order failed for {symbol}: {e}")
