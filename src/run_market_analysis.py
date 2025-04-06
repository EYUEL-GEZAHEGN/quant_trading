import os
import sys
import time
import logging
import argparse
from datetime import datetime
import pytz
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import the modules
from market_ticker_query import MarketTickerQuery
from open_market_loader import OpenMarketLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
EASTERN = pytz.timezone('US/Eastern')
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
ANALYSIS_START_TIME = "10:15"  # 45 minutes after market open

def get_market_status():
    """Get current market status."""
    now = datetime.now(EASTERN)
    current_time = now.strftime("%H:%M")
    current_day = now.strftime("%A")
    
    # Check if it's a weekend
    is_weekend = current_day in ["Saturday", "Sunday"]
    
    # Determine market status
    if is_weekend:
        status = "closed"
    elif current_time < MARKET_OPEN:
        status = "pre-market"
    elif MARKET_OPEN <= current_time < MARKET_CLOSE:
        status = "open"
    elif MARKET_CLOSE <= current_time < "20:00":
        status = "post-market"
    else:
        status = "closed"
    
    # Check if we're in the analysis period
    is_analysis_time = MARKET_OPEN <= current_time < ANALYSIS_START_TIME
    
    return {
        "status": status,
        "current_time": current_time,
        "current_day": current_day,
        "is_weekend": is_weekend,
        "is_analysis_time": is_analysis_time
    }

def run_market_ticker_query(max_symbols=100):
    """Run the market ticker query."""
    logger.info("Starting market ticker query...")
    
    # Create the market ticker query
    mtq = MarketTickerQuery()
    
    # Analyze the market
    results = mtq.analyze_market(max_symbols=max_symbols)
    
    # Print top 10 symbols
    print("\nTop 10 symbols primed for trading:")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['symbol']} (Score: {result['score']:.2f})")
        print(f"   Signals: {', '.join(result['signals'])}")
    
    logger.info("Market ticker query completed")
    return results

def run_open_market_loader():
    """Run the open market loader."""
    logger.info("Starting open market loader...")
    
    # Create the open market loader
    oml = OpenMarketLoader()
    
    # Get market status
    market_status = oml._get_market_status()
    logger.info(f"Current market status: {market_status['status']}")
    
    # Check if market is open
    if market_status["status"] != "open":
        logger.warning(f"Market is {market_status['status']}. Analysis will start when market opens.")
        return
    
    # Check if we're in the analysis period
    if market_status["is_analysis_time"]:
        # Analyze symbols
        signals = oml.analyze_symbols()
        
        # Print tradeable symbols
        if signals:
            print("\nTradeable symbols:")
            for i, signal in enumerate(signals, 1):
                action = "BUY" if signal["buy"] else "SELL"
                print(f"{i}. {signal['symbol']}: {action} (Strength: {signal['strength']:.2f})")
                print(f"   Signals: {', '.join(signal['signals'])}")
        else:
            print("\nNo tradeable symbols found.")
    else:
        # Start the analysis process
        if oml.start_analysis():
            print("\nMarket analysis started. Waiting for 10:15 AM Eastern time...")
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                oml.stop_analysis()
                print("\nMarket analysis stopped.")
    
    logger.info("Open market loader completed")

def main():
    """Main function to run the market analysis."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run market analysis')
    parser.add_argument('--mode', type=str, choices=['query', 'loader', 'both'], default='both',
                        help='Mode to run: query (market ticker query), loader (open market loader), or both')
    parser.add_argument('--max-symbols', type=int, default=100,
                        help='Maximum number of symbols to analyze')
    parser.add_argument('--wait', action='store_true',
                        help='Wait for market to open if it is closed')
    
    args = parser.parse_args()
    
    # Get market status
    market_status = get_market_status()
    logger.info(f"Current market status: {market_status['status']}")
    
    # Check if market is closed and wait is not specified
    if market_status["status"] == "closed" and not args.wait:
        logger.warning("Market is closed. Use --wait to wait for market to open.")
        return
    
    # Wait for market to open if specified
    if market_status["status"] == "closed" and args.wait:
        logger.info("Waiting for market to open...")
        while market_status["status"] == "closed":
            time.sleep(60)
            market_status = get_market_status()
        logger.info(f"Market is now {market_status['status']}")
    
    # Run the market ticker query
    if args.mode in ['query', 'both']:
        run_market_ticker_query(max_symbols=args.max_symbols)
    
    # Run the open market loader
    if args.mode in ['loader', 'both']:
        run_open_market_loader()

if __name__ == "__main__":
    main() 