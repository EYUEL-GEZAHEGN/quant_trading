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



# Performance metrics
class PerformanceMetrics:
    def __init__(self):
        self.trades = []
        self.daily_returns = []
        self.win_rate = 0.0
        self.profit_factor = 0.0
        self.max_drawdown = 0.0
        self.sharpe_ratio = 0.0
        
    def add_trade(self, symbol, entry_price, exit_price, entry_time, exit_time, strategy):
        """Add a trade to the metrics."""
        trade = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'strategy': strategy,
            'return': (exit_price - entry_price) / entry_price
        }
        self.trades.append(trade)
        self._update_metrics()
        
    def _update_metrics(self):
        """Update performance metrics based on trades."""
        if not self.trades:
            return
            
        # Calculate win rate
        winning_trades = sum(1 for t in self.trades if t['return'] > 0)
        self.win_rate = winning_trades / len(self.trades)
        
        # Calculate profit factor
        gross_profit = sum(t['return'] for t in self.trades if t['return'] > 0)
        gross_loss = abs(sum(t['return'] for t in self.trades if t['return'] < 0))
        self.profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        # Calculate max drawdown
        cumulative_returns = [1 + t['return'] for t in self.trades]
        for i in range(1, len(cumulative_returns)):
            cumulative_returns[i] *= cumulative_returns[i-1]
        
        peak = cumulative_returns[0]
        max_dd = 0
        for value in cumulative_returns:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
        self.max_drawdown = max_dd
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0.02)
        returns = [t['return'] for t in self.trades]
        if returns:
            avg_return = sum(returns) / len(returns)
            std_dev = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            self.sharpe_ratio = (avg_return - 0.02) / std_dev if std_dev != 0 else 0
            
    def get_summary(self):
        """Get a summary of performance metrics."""
        return {
            'total_trades': len(self.trades),
            'win_rate': f"{self.win_rate:.2%}",
            'profit_factor': f"{self.profit_factor:.2f}",
            'max_drawdown': f"{self.max_drawdown:.2%}",
            'sharpe_ratio': f"{self.sharpe_ratio:.2f}"
        }

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

def analyze_last_trading_day():
    """Analyze the last trading day's data to identify potential stocks for the next trading day."""
    logger.info("Analyzing last trading day's data...")
    
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
    
    # Create the market ticker query
    mtq = MarketTickerQuery()
    
    # Analyze the market for the last trading day
    results = mtq.analyze_symbols(max_symbols=config["max_symbols"])
    
    # Print top 10 symbols
    print("\nTop 10 symbols for next trading day:")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['symbol']} (Score: {result['score']:.2f})")
        print(f"   Signals: {', '.join(result['signals'])}")
    
    # Get top symbols
    top_symbols = mtq.get_top_symbols(top_n=10)
    print("\nTop 10 symbols for further analysis:")
    for i, symbol in enumerate(top_symbols, 1):
        print(f"{i}. {symbol}")
    
    logger.info("Last trading day analysis completed")
    return top_symbols

def run_market_analysis(max_symbols=100):
    """Run the market analysis system to identify stocks primed for trading."""
    logger.info("Starting market analysis system...")
    
    # Create the market ticker query
    mtq = MarketTickerQuery()
    
    # Analyze the market
    results = mtq.analyze_market(max_symbols=max_symbols)
    
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
    
    logger.info("Market analysis completed")
    return top_symbols

def run_open_market_analysis(top_symbols=None):
    """Run the open market loader to analyze the identified stocks during market hours."""
    logger.info("Starting open market loader...")
    
    # Create the open market loader
    oml = OpenMarketLoader()
    
    # Get market status
    market_status = oml._get_market_status()
    logger.info(f"Current market status: {market_status['status']}")
    
    # Check if market is open
    if market_status["status"] != "open":
        logger.warning(f"Market is {market_status['status']}. Analysis will start when market opens.")
        return []
    
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
        
        return signals
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
        
        return []

def backtest_strategies(symbols, start_date, end_date):
    """Backtest multiple strategies on a list of symbols."""
    logger.info(f"Backtesting strategies on {len(symbols)} symbols...")
    
    results = {}
    
    for strategy_name, StrategyClass in STRATEGIES.items():
        logger.info(f"Backtesting {strategy_name} strategy...")
        
        strategy_results = []
        for symbol in symbols:
            try:
                # Special handling for stat_arb strategy
                if strategy_name == 'stat_arb':
                    # For stat_arb, we need a pair symbol
                    # You could modify this to get the pair from somewhere else
                    pair_symbol = f"{symbol}_PAIR"  # This is just a placeholder
                    strategy = StrategyClass(symbol, pair_symbol)
                else:
                    strategy = StrategyClass(symbol)
                
                # Run the backtest
                result = run_backtest(strategy, symbol, start_date, end_date)
                strategy_results.append(result)
            except Exception as e:
                logger.error(f"Error backtesting {strategy_name} on {symbol}: {str(e)}")
                continue
        
        if strategy_results:
            # Calculate average performance
            avg_return = sum(r['return'] for r in strategy_results) / len(strategy_results)
            avg_sharpe = sum(r['sharpe_ratio'] for r in strategy_results) / len(strategy_results)
            avg_drawdown = sum(r['max_drawdown'] for r in strategy_results) / len(strategy_results)
            
            results[strategy_name] = {
                'avg_return': avg_return,
                'avg_sharpe': avg_sharpe,
                'avg_drawdown': avg_drawdown,
                'symbols': [r['symbol'] for r in strategy_results]
            }
    
    # Print results
    if results:
        print("\nStrategy Performance Summary:")
        for strategy_name, result in results.items():
            print(f"\n{strategy_name}:")
            print(f"  Average Return: {result['avg_return']:.2%}")
            print(f"  Average Sharpe Ratio: {result['avg_sharpe']:.2f}")
            print(f"  Average Max Drawdown: {result['avg_drawdown']:.2%}")
            print(f"  Top Performing Symbols: {', '.join(result['symbols'][:5])}")
        
        # Find the best strategy
        best_strategy = max(results.items(), key=lambda x: x[1]['avg_return'])
        print(f"\nBest Strategy: {best_strategy[0]} (Return: {best_strategy[1]['avg_return']:.2%})")
    else:
        print("\nNo successful backtest results.")
    
    return results