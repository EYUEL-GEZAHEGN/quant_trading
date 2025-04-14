from strategy.crypto_strategy import CryptoMomentumStrategy
from data_loader.live import start_streaming, get_latest_bar
from trade_executor.executor import AlpacaClient
import time

strategy = CryptoMomentumStrategy()
symbols = strategy.get_target_symbols()

# Start WebSocket and stream
if not start_streaming(symbols):
    exit()

print(f"🚀 Live trading started for symbols: {symbols}")

executor = AlpacaClient()
last_signal_time = {}
TRADE_COOLDOWN = 60  # seconds

while True:
    for symbol in symbols:
        bar = get_latest_bar(symbol)
        if bar is None or bar.empty:
            continue

        print(f"📊 Latest bar for {symbol}:\n{bar}")  # <--- add this to verify
        signal = strategy.generate_signal(symbol, bar)

        if signal == "BUY":
            print(f"🚀 {symbol} signal is BUY — submitting order")
            executor.submit_order(symbol, qty=1, side="BUY")
            last_signal_time[symbol] = time.time()
        elif signal == "SELL":
            print(f"🔻 {symbol} signal is SELL — submitting order")
            executor.submit_order(symbol, qty=1, side="SELL")

    time.sleep(5)
