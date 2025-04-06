import os
import sys
import time
import logging
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import database utilities
from db.utils import init_db

# Import market analysis modules
from market_ticker_query import MarketTickerQuery
from open_market_loader import OpenMarketLoader

# Import trading strategy modules
from strategy.mean_reversion import MeanReversionBot
from strategy.breakout import BreakoutBot
from strategy.stat_arb import StatArbBot
from strategy.sentiment_strategy import SentimentBot
from strategy.ta_strategy import TAIndicatorStrategy
from strategy.mixed_signal import MixedSignalsStrategy
from strategy.harris_candles import HarrisCandlesStrategy

# Import backtest and live trading modules
from backtest.engine import run_backtest
from live_trading.executor import run_live_trading

# Import Performance

from performance import PerformanceMetrics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("quant_trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
EASTERN = pytz.timezone('US/Eastern')
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
ANALYSIS_START_TIME = "10:15"  # 45 minutes after market open
ANALYSIS_END_TIME = "15:45"    # 15 minutes before market close
ANALYSIS_INTERVAL = 300  # 5 minutes in seconds

# Available trading strategies
STRATEGIES = {
    'mean_reversion': MeanReversionBot,
    'breakout': BreakoutBot,
    'stat_arb': StatArbBot,
    'sentiment': SentimentBot,
    'ta_indicator': TAIndicatorStrategy,
    'mixed_signals': MixedSignalsStrategy,
    'harris': HarrisCandlesStrategy
}

# Configuration
config = {
    "max_symbols": int(os.getenv("MAX_SYMBOLS", "100")),
    "min_volume": int(os.getenv("MIN_VOLUME", "50000")),
    "min_price": float(os.getenv("MIN_PRICE", "5.0")),
    "volatility_threshold": float(os.getenv("VOLATILITY_THRESHOLD", "0.01")),
    "momentum_threshold": float(os.getenv("MOMENTUM_THRESHOLD", "0.005")),
    "trading_mode": os.getenv("TRADING_MODE", "paper"),
    "strategy": os.getenv("STRATEGY", "mean_reversion"),
    "symbol": os.getenv("SYMBOL", "TQQQ"),
    "pair_symbol": os.getenv("PAIR_SYMBOL", "SQQQ")
}

def main():
    """Main function to run the market analysis system."""
    # Initialize the database
    init_db()
    
    # Initialize performance metrics
    metrics = PerformanceMetrics()
    
    # Get market status
    market_status = get_market_status()
    logger.info(f"Current market status: {market_status['status']}")
    
    # Check if market is open
    if market_status["status"] == "open":
        logger.info("Market is open. Running real-time analysis...")
        
        # Check if we're in the analysis period
        if market_status["is_analysis_time"]:
            # Run market analysis to identify stocks
            top_symbols = run_market_analysis(max_symbols=config["max_symbols"])
            
            # Run open market analysis on identified stocks
            signals = run_open_market_analysis(top_symbols)
            
            # Print summary
            if signals:
                print("\nAnalysis Summary:")
                print(f"Found {len(signals)} tradeable symbols")
                print("Use these signals to execute trades using your preferred strategy")
            else:
                print("\nNo tradeable symbols found")
        else:
            # Start continuous analysis
            print("\nStarting continuous market analysis...")
            try:
                # Run market analysis first
                top_symbols = run_market_analysis(max_symbols=config["max_symbols"])
                
                # Start open market analysis
                run_open_market_analysis(top_symbols)
            except KeyboardInterrupt:
                print("\nMarket analysis stopped by user")
                sys.exit(0)
    else:
        logger.info("Market is closed. Analyzing last trading day...")
        
        # Analyze the last trading day
        top_symbols = analyze_last_trading_day()
        
        # Get the last trading day
        now = datetime.now(EASTERN)
        current_day = now.strftime("%A")
        
        # Calculate the last trading day
        if current_day == "Saturday":
            # If Saturday, go back 1 day to Friday
            last_trading_day = now - timedelta(days=1)
        elif current_day == "Sunday":
            # If Sunday, go back 2 days to Friday
            last_trading_day = now - timedelta(days=2)
        elif current_day == "Monday" and now.strftime("%H:%M") < MARKET_OPEN:
            # If Monday before market open, go back 3 days to Friday
            last_trading_day = now - timedelta(days=3)
        else:
            # For other days, go back 1 day
            last_trading_day = now - timedelta(days=1)
        
        # Format dates for backtesting
        start_date = last_trading_day.strftime("%Y-%m-%d")
        end_date = last_trading_day.strftime("%Y-%m-%d")
        
        # Backtest strategies on the top symbols
        backtest_results = backtest_strategies(top_symbols, start_date, end_date)
        
        # Print performance metrics
        print("\nPerformance Metrics:")
        metrics_summary = metrics.get_summary()
        for metric, value in metrics_summary.items():
            print(f"{metric}: {value}")
        
        # Wait for market to open
        print("\nWaiting for market to open...")
        while True:
            market_status = get_market_status()
            if market_status["status"] == "open":
                logger.info("Market is now open. Starting real-time analysis...")
                break
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
