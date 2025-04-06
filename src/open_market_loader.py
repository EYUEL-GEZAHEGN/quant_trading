import os
import sys
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import pytz
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from pathlib import Path
import time
import threading
import queue
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from dotenv import load_dotenv

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
        logging.FileHandler("open_market_loader.log"),
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

class OpenMarketLoader:
    """
    Analyzes the list of stocks identified by the market ticker query
    and determines which ones to trade after 10:15 AM Eastern time.
    """
    
    def __init__(self, 
                 data_dir: str = "data/market_analysis",
                 results_dir: str = "data/trading_signals",
                 cache_dir: str = "data/cache",
                 min_volume: int = 50000,
                 min_price: float = 5.0,
                 volatility_threshold: float = 0.01,
                 momentum_threshold: float = 0.005,
                 max_symbols: int = 5):
        """
        Initialize the OpenMarketLoader class.
        
        Args:
            data_dir: Directory to store market analysis data
            results_dir: Directory to store trading signals
            cache_dir: Directory to store cached data
            min_volume: Minimum volume for a stock to be considered
            min_price: Minimum price for a stock to be considered
            volatility_threshold: Threshold for volatility
            momentum_threshold: Threshold for momentum
            max_symbols: Maximum number of symbols to analyze
        """
        # Set up directories
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set parameters
        self.min_volume = min_volume
        self.min_price = min_price
        self.volatility_threshold = volatility_threshold
        self.momentum_threshold = momentum_threshold
        self.max_symbols = max_symbols
        
        # Initialize Alpaca clients
        self.api_key = os.getenv("ALPACA_API_KEY_ID")  # Updated to match .env file
        self.api_secret = os.getenv("ALPACA_SECRET_KEY")  # Updated to match .env file
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not self.api_key or not self.api_secret:
            logger.error("Alpaca API credentials not found. Please set ALPACA_API_KEY_ID and ALPACA_SECRET_KEY environment variables.")
            raise ValueError("Alpaca API credentials not found")
        
        self.historical_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        self.trading_client = TradingClient(self.api_key, self.api_secret, paper=True)
        
        # Initialize database
        self.db = MarketDataDB()
        
        # Initialize analysis thread
        self.analysis_thread = None
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        self.signals = []
        
        logger.info("OpenMarketLoader initialized")
    
    def _get_market_status(self) -> Dict[str, Any]:
        """Get current market status (open, closed, pre-market, post-market)."""
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
        is_analysis_time = MARKET_OPEN <= current_time < ANALYSIS_END_TIME
        
        return {
            "status": status,
            "current_time": current_time,
            "current_day": current_day,
            "is_weekend": is_weekend,
            "is_analysis_time": is_analysis_time
        }
    
    def _load_top_symbols(self) -> List[str]:
        """Load the top symbols from the latest market analysis."""
        # Try to get symbols from database first
        latest_analysis = self.db.get_latest_market_analysis(limit=self.max_symbols * 2)
        if latest_analysis:
            top_symbols = [result["symbol"] for result in latest_analysis]
            logger.info(f"Loaded {len(top_symbols)} top symbols from database")
            return top_symbols
        
        # Fallback to file-based approach
        summary_filepath = self.data_dir / "latest_analysis.json"
        
        if not summary_filepath.exists():
            logger.warning("No analysis results found. Run market_ticker_query.py first.")
            return []
        
        with open(summary_filepath, 'r') as f:
            results = json.load(f)
        
        # Sort by score and get top N
        results.sort(key=lambda x: x["score"], reverse=True)
        top_symbols = [result["symbol"] for result in results[:self.max_symbols * 2]]  # Get twice as many for filtering
        
        logger.info(f"Loaded {len(top_symbols)} top symbols from market analysis")
        return top_symbols
    
    def _get_intraday_data(self, symbol: str, interval: str = "1m") -> Optional[pd.DataFrame]:
        """Get intraday data for a symbol using Alpaca API."""
        try:
            # Get today's date
            today = datetime.now(EASTERN).strftime("%Y-%m-%d")
            
            # Map interval to TimeFrame
            timeframe_map = {
                "1m": TimeFrame.Minute,
                "5m": TimeFrame.Minute(5),
                "15m": TimeFrame.Minute(15),
                "30m": TimeFrame.Minute(30),
                "1h": TimeFrame.Hour,
                "1d": TimeFrame.Day
            }
            
            timeframe = timeframe_map.get(interval, TimeFrame.Minute)
            
            # Create request for intraday data
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=today,
                end=today,
                adjustment=Adjustment.ALL
            )
            
            # Get the data
            bars = self.historical_client.get_stock_bars(request_params)
            
            # Convert to DataFrame
            if bars and symbol in bars:
                df = bars[symbol].df
                return df
            return None
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {str(e)}")
            return None
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for analysis."""
        if df.empty:
            return df
        
        try:
            # Calculate basic indicators
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['rsi'] = self._calculate_rsi(df['close'])
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            
            # Calculate MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp1 - exp2
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # Calculate Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_upper'] = df['bb_middle'] + 2 * df['close'].rolling(window=20).std()
            df['bb_lower'] = df['bb_middle'] - 2 * df['close'].rolling(window=20).std()
            
            # Calculate momentum
            df['momentum'] = df['close'] - df['close'].shift(10)
            
            return df
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return df
    
    def _generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on technical analysis."""
        signals = {
            "buy": False,
            "sell": False,
            "strength": 0,
            "signals": []
        }
        
        if df.empty or len(df) < 50:  # Need at least 50 data points for reliable signals
            return signals
        
        try:
            # Get latest values
            current_price = df['close'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            sma_50 = df['sma_50'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            macd = df['macd'].iloc[-1]
            signal = df['signal'].iloc[-1]
            momentum = df['momentum'].iloc[-1]
            volume_ma = df['volume_ma'].iloc[-1]
            
            # Initialize signal strength
            buy_strength = 0
            sell_strength = 0
            
            # Check moving averages
            if current_price > sma_20 and sma_20 > sma_50:
                buy_strength += 1
                signals["signals"].append("Bullish MA crossover")
            elif current_price < sma_20 and sma_20 < sma_50:
                sell_strength += 1
                signals["signals"].append("Bearish MA crossover")
            
            # Check RSI
            if rsi < 30:
                buy_strength += 1
                signals["signals"].append("Oversold (RSI)")
            elif rsi > 70:
                sell_strength += 1
                signals["signals"].append("Overbought (RSI)")
            
            # Check MACD
            if macd > signal:
                buy_strength += 1
                signals["signals"].append("Bullish MACD")
            elif macd < signal:
                sell_strength += 1
                signals["signals"].append("Bearish MACD")
            
            # Check volume
            if current_volume > volume_ma * 1.5:
                if momentum > 0:
                    buy_strength += 1
                    signals["signals"].append("High volume with upward momentum")
                elif momentum < 0:
                    sell_strength += 1
                    signals["signals"].append("High volume with downward momentum")
            
            # Check Bollinger Bands
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            
            if current_price < bb_lower:
                buy_strength += 1
                signals["signals"].append("Price below lower Bollinger Band")
            elif current_price > bb_upper:
                sell_strength += 1
                signals["signals"].append("Price above upper Bollinger Band")
            
            # Determine final signals
            if buy_strength > sell_strength and buy_strength >= 2:
                signals["buy"] = True
                signals["strength"] = buy_strength / 5  # Normalize to 0-1 range
            elif sell_strength > buy_strength and sell_strength >= 2:
                signals["sell"] = True
                signals["strength"] = sell_strength / 5  # Normalize to 0-1 range
            
            return signals
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return signals
    
    def _calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        try:
            delta = prices.diff()
            
            # Get gains and losses
            gains = delta.copy()
            losses = delta.copy()
            
            gains[gains < 0] = 0
            losses[losses > 0] = 0
            losses = abs(losses)
            
            # Calculate average gains and losses
            avg_gains = gains.rolling(window=periods).mean()
            avg_losses = losses.rolling(window=periods).mean()
            
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
    def _generate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on technical indicators."""
        if data.empty:
            return {
                "buy": False,
                "sell": False,
                "strength": 0,
                "signals": [],
                "is_tradeable": False
            }
        
        # Get the latest data point
        latest = data.iloc[-1]
        
        # Initialize signals
        signals = {
            "buy": False,
            "sell": False,
            "strength": 0,
            "signals": [],
            "is_tradeable": False
        }
        
        # Check for buy signals
        buy_signals = 0
        total_signals = 0
        
        # RSI oversold
        if latest['RSI'] < 30:
            buy_signals += 1
            total_signals += 1
            signals["signals"].append("RSI oversold")
        
        # MACD crossover
        if data['MACD'].iloc[-2] < data['Signal_Line'].iloc[-2] and latest['MACD'] > latest['Signal_Line']:
            buy_signals += 1
            total_signals += 1
            signals["signals"].append("MACD bullish crossover")
        
        # Price below lower Bollinger Band
        if latest['close'] < latest['BB_Lower']:
            buy_signals += 1
            total_signals += 1
            signals["signals"].append("Price below lower Bollinger Band")
        
        # Moving average crossover
        if data['SMA5'].iloc[-2] < data['SMA20'].iloc[-2] and latest['SMA5'] > latest['SMA20']:
            buy_signals += 1
            total_signals += 1
            signals["signals"].append("SMA bullish crossover")
        
        # High volume
        if latest['Volume_Ratio'] > 2:
            buy_signals += 1
            total_signals += 1
            signals["signals"].append("High volume")
        
        # Check for sell signals
        sell_signals = 0
        
        # RSI overbought
        if latest['RSI'] > 70:
            sell_signals += 1
            total_signals += 1
            signals["signals"].append("RSI overbought")
        
        # MACD bearish crossover
        if data['MACD'].iloc[-2] > data['Signal_Line'].iloc[-2] and latest['MACD'] < latest['Signal_Line']:
            sell_signals += 1
            total_signals += 1
            signals["signals"].append("MACD bearish crossover")
        
        # Price above upper Bollinger Band
        if latest['close'] > latest['BB_Upper']:
            sell_signals += 1
            total_signals += 1
            signals["signals"].append("Price above upper Bollinger Band")
        
        # Moving average bearish crossover
        if data['SMA5'].iloc[-2] > data['SMA20'].iloc[-2] and latest['SMA5'] < latest['SMA20']:
            sell_signals += 1
            total_signals += 1
            signals["signals"].append("SMA bearish crossover")
        
        # Determine if the symbol is tradeable
        if total_signals >= 2:
            signals["is_tradeable"] = True
        
        # Determine buy/sell signal
        if buy_signals > sell_signals and buy_signals >= 2:
            signals["buy"] = True
            signals["strength"] = buy_signals / total_signals
        elif sell_signals > buy_signals and sell_signals >= 2:
            signals["sell"] = True
            signals["strength"] = sell_signals / total_signals
        
        return signals
    
    def _analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """Analyze a symbol during market hours."""
        logger.info(f"Analyzing {symbol}...")
        
        # Get intraday data
        df = self._get_intraday_data(symbol)
        
        if df is None or df.empty:
            logger.warning(f"No data available for {symbol}")
            return None
        
        # Calculate technical indicators
        df = self._calculate_technical_indicators(df)
        
        # Generate signals
        signals = self._generate_signals(df)
        
        # Add symbol and analysis time to signals
        signals["symbol"] = symbol
        signals["analysis_time"] = datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
        signals["price"] = df["close"].iloc[-1] if not df.empty else 0
        signals["volume"] = df["volume"].iloc[-1] if not df.empty else 0
        
        return signals
    
    def _save_trading_signals(self, signals: List[Dict[str, Any]]) -> None:
        """Save trading signals to the database and file."""
        if not signals:
            logger.warning("No signals to save")
            return
        
        # Save to database
        self.db.save_trading_signals(signals)
        
        # Also save to file for backward compatibility
        now = datetime.now(EASTERN)
        filename = f"trading_signals_{now.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(signals, f, indent=2)
        
        logger.info(f"Saved {len(signals)} trading signals to {filepath}")
        
        # Also save a summary file
        summary_filepath = self.results_dir / "latest_signals.json"
        with open(summary_filepath, 'w') as f:
            json.dump(signals, f, indent=2)
        
        logger.info(f"Summary saved to {summary_filepath}")
    
    def _data_collector(self, symbols: List[str]):
        """Collect real-time data for the symbols."""
        logger.info(f"Starting data collection for {len(symbols)} symbols")
        
        while not self.stop_event.is_set():
            try:
                for symbol in symbols:
                    # Get intraday data
                    df = self._get_intraday_data(symbol)
                    
                    if df is not None and not df.empty:
                        # Add to queue
                        self.data_queue.put((symbol, df))
                    
                    # Sleep to avoid rate limiting
                    time.sleep(0.1)
                
                # Sleep for the analysis interval
                time.sleep(ANALYSIS_INTERVAL)
            except Exception as e:
                logger.error(f"Error in data collector: {str(e)}")
                time.sleep(ANALYSIS_INTERVAL)
    
    def _analysis_worker(self):
        """Analyze the data in the queue."""
        logger.info("Starting analysis worker")
        
        while not self.stop_event.is_set():
            try:
                # Check if queue is empty
                if self.data_queue.empty():
                    time.sleep(1)
                    continue
                
                # Get data from queue
                symbol, df = self.data_queue.get()
                
                # Calculate technical indicators
                df = self._calculate_technical_indicators(df)
                
                # Generate signals
                signals = self._generate_signals(df)
                
                # Add symbol and analysis time to signals
                signals["symbol"] = symbol
                signals["analysis_time"] = datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
                signals["price"] = df["close"].iloc[-1] if not df.empty else 0
                signals["volume"] = df["volume"].iloc[-1] if not df.empty else 0
                
                # Save signals
                self._save_trading_signals([signals])
                
                # Sleep to avoid rate limiting
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in analysis worker: {str(e)}")
                time.sleep(1)
    
    def start_analysis(self):
        """Start the analysis process."""
        # Get market status
        market_status = self._get_market_status()
        
        # Check if market is open
        if market_status["status"] != "open":
            logger.warning(f"Market is {market_status['status']}. Analysis will start when market opens.")
            return False
        
        # Check if analysis is already running
        if self.analysis_thread and not self.stop_event.is_set():
            logger.warning("Analysis is already running.")
            return False
        
        # Load top symbols
        symbols = self._load_top_symbols()
        
        if not symbols:
            logger.error("No symbols to analyze.")
            return False
        
        # Start the analysis thread
        self.stop_event.clear()
        self.analysis_thread = threading.Thread(target=self._analysis_worker)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        # Start the data collector thread
        self.data_collector_thread = threading.Thread(target=self._data_collector, args=(symbols,))
        self.data_collector_thread.daemon = True
        self.data_collector_thread.start()
        
        logger.info("Analysis started.")
        return True
    
    def stop_analysis(self):
        """Stop the analysis process."""
        # Check if analysis is running
        if not self.analysis_thread or self.stop_event.is_set():
            logger.warning("Analysis is not running.")
            return False
        
        # Stop the analysis thread
        self.stop_event.set()
        
        # Wait for threads to finish
        if self.analysis_thread:
            self.analysis_thread.join(timeout=10)
        
        if self.data_collector_thread:
            self.data_collector_thread.join(timeout=10)
        
        logger.info("Analysis stopped.")
        return True
    
    def analyze_symbols(self) -> List[Dict[str, Any]]:
        """Analyze the top symbols from the market ticker query."""
        # Get market status
        market_status = self._get_market_status()
        
        # Check if market is open
        if market_status["status"] != "open":
            logger.warning(f"Market is {market_status['status']}. Analysis will start when market opens.")
            return []
        
        # Load top symbols
        symbols = self._load_top_symbols()
        
        if not symbols:
            logger.error("No symbols to analyze.")
            return []
        
        # Analyze each symbol
        signals = []
        for symbol in symbols:
            try:
                signal = self._analyze_symbol(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
            
            # Sleep to avoid rate limiting
            time.sleep(0.1)
        
        # Save signals
        if signals:
            self._save_trading_signals(signals)
        
        return signals
    
    def get_latest_signals(self) -> List[Dict[str, Any]]:
        """Get the latest trading signals from the database."""
        # Try to get signals from database first
        latest_signals = self.db.get_latest_trading_signals(limit=10)
        if latest_signals:
            return latest_signals
        
        # Fallback to file-based approach
        summary_filepath = self.results_dir / "latest_signals.json"
        
        if not summary_filepath.exists():
            logger.warning("No trading signals found.")
            return []
        
        with open(summary_filepath, 'r') as f:
            signals = json.load(f)
        
        return signals

def main():
    """Main function to run the open market loader."""
    # Create the open market loader
    oml = OpenMarketLoader()
    
    # Get market status
    market_status = oml._get_market_status()
    logger.info(f"Current market status: {market_status['status']}")
    
    # Check if market is open
    if market_status["status"] != "open":
        logger.warning(f"Market is {market_status['status']}. Analysis will start when market opens.")
        sys.exit(1)
    
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

if __name__ == "__main__":
    main() 