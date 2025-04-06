import os
import sys
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import database utility
from db.market_data_db import MarketDataDB

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_ticker_query.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
EASTERN = pytz.timezone('US/Eastern')
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
ANALYSIS_START_TIME = "10:15"  # 45 minutes after market open

class MarketTickerQuery:
    """Class to query and analyze market tickers."""
    
    def __init__(self):
        """Initialize the MarketTickerQuery class."""
        # Initialize Alpaca client
        self.api_key = os.getenv("ALPACA_API_KEY_ID")
        self.api_secret = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not self.api_key or not self.api_secret:
            logger.error("Alpaca API credentials not found. Please set ALPACA_API_KEY_ID and ALPACA_SECRET_KEY environment variables.")
            raise ValueError("Alpaca API credentials not found")
        
        self.client = StockHistoricalDataClient(self.api_key, self.api_secret)
        
        # Initialize database
        self.db = MarketDataDB()
        
        # Initialize results
        self.results = []
        self.top_symbols = []
    
    def _get_market_status(self):
        """
        Get the current market status.
        
        Returns:
            dict: Market status information
        """
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
    
    def _get_pre_market_data(self, symbol):
        """
        Get pre-market data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame: Pre-market data
        """
        try:
            # Get current date in Eastern time
            now = datetime.now(EASTERN)
            # If it's before market open, get today's data
            # Otherwise, get next day's data
            if now.strftime("%H:%M") < MARKET_OPEN:
                today = now.strftime("%Y-%m-%d")
            else:
                today = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Create request for pre-market data
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=datetime.strptime(f"{today} 04:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=EASTERN) - timedelta(days=1),
                end=datetime.strptime(f"{today} 09:30:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=EASTERN),
                adjustment=Adjustment.ALL
            )
            
            # Get the data
            bars = self.client.get_stock_bars(request_params)
            
            # Convert to DataFrame
            if bars and symbol in bars:
                df = bars[symbol].df
                return df
            else:
                logger.warning(f"No pre-market data found for {symbol}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting pre-market data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _get_post_market_data(self, symbol):
        """
        Get post-market data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame: Post-market data
        """
        try:
            # Get current date in Eastern time
            now = datetime.now(EASTERN)
            # If it's after market close, get today's data
            # Otherwise, get previous day's data
            if now.strftime("%H:%M") > MARKET_CLOSE:
                today = now.strftime("%Y-%m-%d")
            else:
                today = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Create request for post-market data
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=datetime.strptime(f"{today} 16:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=EASTERN),
                end=datetime.strptime(f"{today} 20:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=EASTERN),
                adjustment=Adjustment.ALL
            )
            
            # Get the data
            bars = self.client.get_stock_bars(request_params)
            
            # Convert to DataFrame
            if bars and symbol in bars:
                df = bars[symbol].df
                return df
            else:
                logger.warning(f"No post-market data found for {symbol}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting post-market data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _get_last_trading_day_data(self, symbol):
        """
        Get the last trading day data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame: Last trading day data
        """
        try:
            # Get current date in Eastern time
            now = datetime.now(EASTERN)
            current_day = now.strftime("%A")
            
            # Calculate the last trading day
            if current_day == "Saturday":
                # If Saturday, go back 1 day to Friday
                end_date = now - timedelta(days=1)
            elif current_day == "Sunday":
                # If Sunday, go back 2 days to Friday
                end_date = now - timedelta(days=2)
            elif current_day == "Monday" and now.strftime("%H:%M") < MARKET_OPEN:
                # If Monday before market open, go back 3 days to Friday
                end_date = now - timedelta(days=3)
            else:
                # For other days, go back 1 day
                end_date = now - timedelta(days=1)
            
            # Format the date
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Create request for daily data - request 10 days of data to ensure we get the last trading day
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=EASTERN) - timedelta(days=10),
                end=datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=EASTERN),
                adjustment=Adjustment.ALL
            )
            
            # Get the data
            bars = self.client.get_stock_bars(request_params)
            
            # Convert to DataFrame
            if bars and symbol in bars:
                df = bars[symbol].df
                # Get the last trading day
                if not df.empty:
                    return df.iloc[-1:]
                else:
                    logger.warning(f"No last trading day data found for {symbol}")
                    return pd.DataFrame()
            else:
                logger.warning(f"No last trading day data found for {symbol}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting last trading day data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_metrics(self, pre_market_df, post_market_df, last_trading_day_df):
        """
        Calculate metrics for a symbol.
        
        Args:
            pre_market_df: Pre-market data (not used)
            post_market_df: Post-market data (not used)
            last_trading_day_df: Last trading day data
            
        Returns:
            dict: Calculated metrics
        """
        metrics = {
            "last_trading_day_volume": 0,
            "last_trading_day_price_change": 0,
            "last_trading_day_price_change_pct": 0,
            "score": 0,
            "signals": []
        }
        
        # Calculate last trading day metrics
        if not last_trading_day_df.empty:
            metrics["last_trading_day_volume"] = last_trading_day_df["volume"].iloc[0]
            metrics["last_trading_day_price_change"] = last_trading_day_df["close"].iloc[0] - last_trading_day_df["open"].iloc[0]
            metrics["last_trading_day_price_change_pct"] = (metrics["last_trading_day_price_change"] / last_trading_day_df["open"].iloc[0]) * 100
            
            # Add signals based on last trading day data
            if metrics["last_trading_day_price_change_pct"] > 3:
                metrics["signals"].append("Strong previous day gain")
            elif metrics["last_trading_day_price_change_pct"] > 0:
                metrics["signals"].append("Previous day gain")
            elif metrics["last_trading_day_price_change_pct"] < -3:
                metrics["signals"].append("Strong previous day loss")
            elif metrics["last_trading_day_price_change_pct"] < 0:
                metrics["signals"].append("Previous day loss")
            
            if metrics["last_trading_day_volume"] > 1000000:
                metrics["signals"].append("High previous day volume")
        
        # Calculate overall score based only on last trading day data
        metrics["score"] = metrics["last_trading_day_price_change_pct"]
        
        return metrics
    
    def analyze_symbols(self, max_symbols=50):
        """
        Analyze market tickers.
        
        Args:
            max_symbols: Maximum number of symbols to analyze
        """
        # Get market status
        market_status = self._get_market_status()
        logger.info(f"Current market status: {market_status['status']}")
        
        # Define list of symbols to analyze
        symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT",
            "PG", "MA", "HD", "BAC", "DIS", "NFLX", "ADBE", "CSCO", "PFE", "INTC",
            "VZ", "KO", "PEP", "T", "ABT", "MRK", "ABBV", "AVGO", "TMO", "QCOM",
            "CVX", "ACN", "LLY", "DHR", "MCD", "NKE", "PM", "UNH", "UPS", "IBM",
            "LOW", "MS", "RTX", "HON", "LMT", "BA", "CAT", "DE", "MMM", "GE"
        ]
        
        # Limit the number of symbols
        symbols = symbols[:max_symbols]
        
        # Analyze each symbol
        self.results = []
        for symbol in symbols:
            logger.info(f"Analyzing {symbol}...")
            
            # Get data - skip pre/post market data
            pre_market_df = pd.DataFrame()  # Empty DataFrame instead of fetching pre-market data
            post_market_df = pd.DataFrame()  # Empty DataFrame instead of fetching post-market data
            last_trading_day_df = self._get_last_trading_day_data(symbol)
            
            # Calculate metrics
            metrics = self._calculate_metrics(pre_market_df, post_market_df, last_trading_day_df)
            
            # Add symbol and market status to metrics
            metrics["symbol"] = symbol
            metrics["analysis_time"] = datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
            metrics["market_status"] = market_status["status"]
            
            # Store data for database
            metrics["pre_market"] = {}  # Empty dict since we're not using pre-market data
            metrics["post_market"] = {}  # Empty dict since we're not using post-market data
            metrics["last_trading_day"] = last_trading_day_df.to_dict() if not last_trading_day_df.empty else {}
            
            # Add to results
            self.results.append(metrics)
            
            # Sleep to avoid rate limiting
            time.sleep(0.1)
        
        # Save results to database
        if self.results:
            self.db.save_market_analysis(self.results)
        
        return self.results
    
    def get_top_symbols(self, top_n=10):
        """
        Get the top symbols from the analysis.
        
        Args:
            top_n: Number of top symbols to return
            
        Returns:
            list: Top symbols
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_symbols() first.")
            return []
        
        return [result["symbol"] for result in self.results[:top_n]]

if __name__ == "__main__":
    # Create the market ticker query
    mtq = MarketTickerQuery()
    
    # Analyze the market
    results = mtq.analyze_symbols(max_symbols=50)
    
    # Print top 10 symbols
    print("\nTop 10 symbols primed for trading:")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['symbol']} (Score: {result['score']:.2f})")
        print(f"   Signals: {', '.join(result['signals'])}")
    
    # Get top symbols
    top_symbols = mtq.get_top_symbols(top_n=10)
    print("\nTop 10 symbols for further analysis:")
    for i, symbol in enumerate(top_symbols, 1):
        print(f"{i}. {symbol}") 