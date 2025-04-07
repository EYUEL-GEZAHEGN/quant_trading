import os
import sys
import logging
from dotenv import load_dotenv

from src.trading.live_trader import LiveTrader
from src.trading.factory import StrategyFactory
from src.utils.logger import setup_logger
from src.market_ticker_query import MarketTickerQuery  # ✅ symbol scorer

def main():
    # Load environment variables from .env
    load_dotenv()

    # Setup logging
    setup_logger()
    logger = logging.getLogger(__name__)

    try:
        # 🎯 Configuration
        strategy_name = os.getenv("STRATEGY", "micro_momentum")
        interval = os.getenv("INTERVAL", "5m")
        max_cvar_threshold = float(os.getenv("MAX_CVAR_THRESHOLD", 0.04))  # 4%
        top_n = int(os.getenv("TOP_N", 10))  # how many symbols to trade

        # 🧠 Rank top tickers using your internal scoring system
        scorer = MarketTickerQuery()
        ranked = scorer.analyze_symbols(max_symbols=50)
        top_symbols = [s["symbol"] for s in ranked if s["score"] > 0.7][:top_n]

        if not top_symbols:
            logger.warning("No top symbols found with score > 0.7")
            sys.exit(1)

        logger.info(f"Top {len(top_symbols)} symbols selected: {top_symbols}")

        # 🔁 Run trader for each selected symbol
        for symbol in top_symbols:
            strategy = StrategyFactory.create_strategy(strategy_name, symbol)
            trader = LiveTrader(strategy, symbol, interval, max_cvar_threshold=max_cvar_threshold)

            logger.info(f"Starting live trading for {symbol} using {strategy_name} strategy with CVaR threshold {max_cvar_threshold}")
            trader.start()

    except Exception as e:
        logger.error(f"❌ Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
