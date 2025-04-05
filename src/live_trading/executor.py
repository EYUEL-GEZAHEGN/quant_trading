from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from db.utils import log_trade
from config import settings
import pandas as pd
import time

trading_client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY, paper=settings.PAPER_TRADING)
data_client = StockHistoricalDataClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)

# Store one open trade's SL/TP levels
open_trade = {}

def run_live_trading(StrategyClass, symbol, live=True):
    print(f"Starting {'LIVE' if live else 'PAPER'} trading for {symbol} using {StrategyClass.__name__}")
    strategy = StrategyClass(symbol)

    while True:
        try:
            # Load market data
            request = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, limit=100)
            bars = data_client.get_stock_bars(request).df

            if bars.empty:
                print("No data returned.")
                time.sleep(60)
                continue

            if 'symbol' in bars.columns:
                bars = bars[bars['symbol'] == symbol].copy()
            else:
                bars = bars.copy()

            # Flatten index if needed
            if isinstance(bars.index, pd.MultiIndex):
                bars.reset_index(inplace=True)
                bars.set_index("timestamp", inplace=True)

            bars.index = pd.to_datetime(bars.index)
            bars.rename(columns={'close': 'close'}, inplace=True)

            signals = strategy.generate_signals(bars)
            last_signal = signals['signal'].iloc[-1]
            current_price = bars['close'].iloc[-1]

            # Initialize previous signal once
            if 'prev_signal' not in locals():
                prev_signal = None

            # Skip trade if signal hasn't changed
            if last_signal == prev_signal:
                print("[HOLD] Same signal as before. No action.")
                time.sleep(5)
                continue

            prev_signal = last_signal

            positions = trading_client.get_all_positions()
            current_position = next((p for p in positions if p.symbol == symbol), None)

            # STOP-LOSS / TAKE-PROFIT logic
            if current_position and open_trade:
                if current_price <= open_trade["stop_price"]:
                    print("🔻 STOP LOSS triggered.")
                    trading_client.submit_order(MarketOrderRequest(
                        symbol=symbol,
                        notional=open_trade["notional"],
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    ))
                    log_trade(symbol, "sell", open_trade["notional"], current_price, StrategyClass.__name__, "stop_loss")
                    open_trade.clear()

                elif current_price >= open_trade["target_price"]:
                    print("🚀 TAKE PROFIT triggered.")
                    trading_client.submit_order(MarketOrderRequest(
                        symbol=symbol,
                        notional=open_trade["notional"],
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    ))
                    log_trade(symbol, "sell", open_trade["notional"], current_price, StrategyClass.__name__, "take_profit")
                    open_trade.clear()

            # ENTRY LOGIC
            elif last_signal == 1 and current_position is None:
                dollar_amount = 1000  # Buy $1000 worth of stock
                stop_pct = 0.02
                target_pct = 0.04
                stop_price = current_price * (1 - stop_pct)
                target_price = current_price * (1 + target_pct)

                print(f"[BUY] ${dollar_amount:.2f} worth of {symbol} at ${current_price:.2f}")
                trading_client.submit_order(MarketOrderRequest(
                    symbol=symbol,
                    notional=dollar_amount,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                ))

                log_trade(symbol, "buy", dollar_amount, current_price, StrategyClass.__name__, "paper" if not live else "live")

                open_trade.update({
                    "symbol": symbol,
                    "notional": dollar_amount,
                    "entry_price": current_price,
                    "stop_price": stop_price,
                    "target_price": target_price
                })

            elif last_signal == -1 and current_position is not None:
                print(f"[SELL] Manual exit signal for {symbol} at ${current_price:.2f}")
                notional = float(current_position.market_value)

                trading_client.submit_order(MarketOrderRequest(
                    symbol=symbol,
                    notional=notional,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                ))

                log_trade(symbol, "sell", notional, current_price, StrategyClass.__name__, "manual_exit")
                open_trade.clear()

            else:
                print("[HOLD] No action taken.")

        except Exception as e:
            print("⚠️ Error during trading loop:", e)

        time.sleep(5)
