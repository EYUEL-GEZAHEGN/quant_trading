import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("settings.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Credentials
ALPACA_API_KEY_ID = os.getenv("ALPACA_API_KEY_ID")  # Updated to match .env file
ALPACA_API_SECRET_KEY = os.getenv("ALPACA_API_SECRET_KEY")  # Updated to match .env file
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
PAPER_TRADING = True

# Print API credentials for debugging
#print(f"API Key: {ALPACA_API_KEY}")
#print(f"Paper Trading: {PAPER_TRADING}")

# Database Configuration
DB_PATH = os.getenv("DB_PATH", "db/market_data.db")

# Market Analysis Configuration
MAX_SYMBOLS = int(os.getenv("MAX_SYMBOLS", "100"))
MIN_VOLUME = int(os.getenv("MIN_VOLUME", "50000"))
MIN_PRICE = float(os.getenv("MIN_PRICE", "5.0"))
VOLATILITY_THRESHOLD = float(os.getenv("VOLATILITY_THRESHOLD", "0.01"))
MOMENTUM_THRESHOLD = float(os.getenv("MOMENTUM_THRESHOLD", "0.005"))

# Trading Configuration
TRADING_MODE = os.getenv("TRADING_MODE", "paper")  # Options: paper, live
STRATEGY = os.getenv("STRATEGY", "harris_candles")  # Options: mean_reversion, breakout, stat_arb, sentiment, technical, mixed
SYMBOL = os.getenv("SYMBOL", "TQQQ")
PAIR_SYMBOL = os.getenv("PAIR_SYMBOL", "SQQQ")  # For stat_arb strategy

# Market Hours
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
ANALYSIS_START_TIME = "10:15"  # 45 minutes after market open
ANALYSIS_END_TIME = "15:45"    # 15 minutes before market close
ANALYSIS_INTERVAL = 300  # 5 minutes in seconds

# Directories
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
LOG_DIR = ROOT_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Data subdirectories
MARKET_ANALYSIS_DIR = DATA_DIR / "market_analysis"
TRADING_SIGNALS_DIR = DATA_DIR / "trading_signals"
CACHE_DIR = DATA_DIR / "cache"

# Create data subdirectories
MARKET_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
TRADING_SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Create necessary directories
def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "db",
        "logs",
        "data",
        "data/historical",
        "data/intraday",
        "data/signals",
        "data/analysis"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

# Create directories
create_directories() 