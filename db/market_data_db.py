import os
import sqlite3
import json
import logging
from datetime import datetime
import pytz
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_operations.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
EASTERN = pytz.timezone('US/Eastern')
DB_DIR = Path("db")
DB_PATH = DB_DIR / "market_data.db"

class MarketDataDB:
    """Database utility for storing market analysis and trading signals."""
    
    def __init__(self, db_path=DB_PATH):
        """
        Initialize the database utility.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        
        # Create the database directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with the required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create market analysis table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_time TEXT NOT NULL,
                market_status TEXT NOT NULL,
                score REAL NOT NULL,
                signals TEXT NOT NULL,
                pre_market_data TEXT,
                post_market_data TEXT,
                last_trading_day_data TEXT,
                created_at TEXT NOT NULL
            )
            ''')
            
            # Create trading signals table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_time TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER NOT NULL,
                buy BOOLEAN NOT NULL,
                sell BOOLEAN NOT NULL,
                strength REAL NOT NULL,
                signals TEXT NOT NULL,
                is_tradeable BOOLEAN NOT NULL,
                created_at TEXT NOT NULL
            )
            ''')
            
            # Create indices for faster queries
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market_analysis_symbol ON market_analysis(symbol)
            ''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market_analysis_time ON market_analysis(analysis_time)
            ''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol ON trading_signals(symbol)
            ''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trading_signals_time ON trading_signals(analysis_time)
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save_market_analysis(self, analysis_results):
        """
        Save market analysis results to the database.
        
        Args:
            analysis_results: List of market analysis results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current time
            now = datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
            
            # Insert each result
            for result in analysis_results:
                cursor.execute('''
                INSERT INTO market_analysis (
                    symbol, analysis_time, market_status, score, signals,
                    pre_market_data, post_market_data, last_trading_day_data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result["symbol"],
                    result["analysis_time"],
                    result["market_status"],
                    result["score"],
                    json.dumps(result["signals"]),
                    json.dumps(result.get("pre_market", {})),
                    json.dumps(result.get("post_market", {})),
                    json.dumps(result.get("last_trading_day", {})),
                    now
                ))
            
            conn.commit()
            logger.info(f"Saved {len(analysis_results)} market analysis results to database")
        except Exception as e:
            logger.error(f"Error saving market analysis to database: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save_trading_signals(self, signals):
        """
        Save trading signals to the database.
        
        Args:
            signals: List of trading signals
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current time
            now = datetime.now(EASTERN).strftime("%Y-%m-%d %H:%M:%S %Z")
            
            # Insert each signal
            for signal in signals:
                cursor.execute('''
                INSERT INTO trading_signals (
                    symbol, analysis_time, price, volume, buy, sell,
                    strength, signals, is_tradeable, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal["symbol"],
                    signal["analysis_time"],
                    signal["price"],
                    signal["volume"],
                    signal["buy"],
                    signal["sell"],
                    signal["strength"],
                    json.dumps(signal["signals"]),
                    signal["is_tradeable"],
                    now
                ))
            
            conn.commit()
            logger.info(f"Saved {len(signals)} trading signals to database")
        except Exception as e:
            logger.error(f"Error saving trading signals to database: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_latest_market_analysis(self, limit=10):
        """
        Get the latest market analysis results.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of market analysis results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM market_analysis
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["signals"] = json.loads(result["signals"])
                result["pre_market_data"] = json.loads(result["pre_market_data"]) if result["pre_market_data"] else {}
                result["post_market_data"] = json.loads(result["post_market_data"]) if result["post_market_data"] else {}
                result["last_trading_day_data"] = json.loads(result["last_trading_day_data"]) if result["last_trading_day_data"] else {}
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting latest market analysis: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_latest_trading_signals(self, limit=10):
        """
        Get the latest trading signals.
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of trading signals
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM trading_signals
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["signals"] = json.loads(result["signals"])
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting latest trading signals: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_market_analysis_by_symbol(self, symbol, limit=10):
        """
        Get market analysis results for a specific symbol.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of results to return
            
        Returns:
            List of market analysis results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM market_analysis
            WHERE symbol = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (symbol, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["signals"] = json.loads(result["signals"])
                result["pre_market_data"] = json.loads(result["pre_market_data"]) if result["pre_market_data"] else {}
                result["post_market_data"] = json.loads(result["post_market_data"]) if result["post_market_data"] else {}
                result["last_trading_day_data"] = json.loads(result["last_trading_day_data"]) if result["last_trading_day_data"] else {}
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting market analysis for {symbol}: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_trading_signals_by_symbol(self, symbol, limit=10):
        """
        Get trading signals for a specific symbol.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of signals to return
            
        Returns:
            List of trading signals
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM trading_signals
            WHERE symbol = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (symbol, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["signals"] = json.loads(result["signals"])
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting trading signals for {symbol}: {str(e)}")
            return []
        finally:
            if conn:
                conn.close() 