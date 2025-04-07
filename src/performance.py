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

# The rest of the main.py logic remains the same...
# (no change needed to the bottom half of your script)

if __name__ == "__main__":
    main()
