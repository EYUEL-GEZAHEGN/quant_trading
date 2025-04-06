import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import argparse
import importlib
import inspect
import json
import os
from typing import Dict, Any, Type, List, Optional

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent))

from backtest.engine import run_backtest
from data_loader import load_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Backtester:
    """
    Generic backtester that can run any strategy with minimal code changes.
    """
    
    def __init__(self, strategy_class: Type, strategy_params: Dict[str, Any] = None):
        """
        Initialize the backtester with a strategy class and parameters.
        
        Args:
            strategy_class: The strategy class to use for backtesting
            strategy_params: Dictionary of parameters to pass to the strategy
        """
        self.strategy_class = strategy_class
        self.strategy_params = strategy_params or {}
        
    def run(self, 
            symbol: str,
            start_date: str,
            end_date: str,
            initial_capital: float = 100000.0,
            plot_results: bool = True,
            save_plot: bool = True,
            plot_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a backtest with the specified parameters.
        
        Args:
            symbol: Trading symbol
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            initial_capital: Initial capital for backtest
            plot_results: Whether to plot the results
            save_plot: Whether to save the plot to a file
            plot_filename: Filename to save the plot to (if None, will use symbol and date)
            
        Returns:
            Dictionary containing backtest results
        """
        logger.info(f"Starting backtest for {symbol} using {self.strategy_class.__name__}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial Capital: ${initial_capital:,.2f}")
        
        # Initialize strategy
        strategy = self.strategy_class(symbol=symbol, **self.strategy_params)
        
        # Run backtest
        results = run_backtest(
            strategy_class=self.strategy_class,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # Print results
        print("\n=== Backtest Results ===")
        print(f"Final Portfolio Value: ${results['final_value']:,.2f}")
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Number of Trades: {len(results.get('trades', []))}")
        
        # Plot results if requested
        if plot_results:
            self._plot_results(symbol, start_date, end_date, results, save_plot, plot_filename)
        
        return results
    
    def _plot_results(self, 
                     symbol: str, 
                     start_date: str, 
                     end_date: str, 
                     results: Dict[str, Any],
                     save_plot: bool = True,
                     plot_filename: Optional[str] = None) -> None:
        """
        Plot the backtest results.
        
        Args:
            symbol: Trading symbol
            start_date: Start date for backtest
            end_date: End date for backtest
            results: Dictionary containing backtest results
            save_plot: Whether to save the plot to a file
            plot_filename: Filename to save the plot to
        """
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Price and Signals
        plt.subplot(2, 1, 1)
        data = load_data(symbol, start_date, end_date)
        strategy = self.strategy_class(symbol=symbol, **self.strategy_params)
        signals = strategy.generate_signals(data)
        
        plt.plot(data.index, data['close'], label='Price', color='blue')
        plt.plot(data[signals['signal'] == 1].index, 
                 data[signals['signal'] == 1]['close'], 
                 '^', color='green', label='Buy Signal')
        plt.plot(data[signals['signal'] == -1].index, 
                 data[signals['signal'] == -1]['close'], 
                 'v', color='red', label='Sell Signal')
        plt.title(f'{symbol} Price and Trading Signals')
        plt.legend()
        plt.grid(True)
        
        # Plot 2: Portfolio Value
        plt.subplot(2, 1, 2)
        portfolio_values = pd.Series(results['equity_curve'])
        plt.plot(portfolio_values.index, portfolio_values.values, 
                 label='Portfolio Value', color='purple')
        plt.title('Portfolio Value Over Time')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_plot:
            if plot_filename is None:
                plot_filename = f'{symbol}_{start_date}_to_{end_date}_backtest_results.png'
            plt.savefig(plot_filename)
            print(f"\nResults plot saved as '{plot_filename}'")
        
        plt.show()

def load_strategy_class(module_path: str, class_name: str) -> Type:
    """
    Load a strategy class from a module.
    
    Args:
        module_path: Path to the module (e.g., 'strategy.ta_strategy')
        class_name: Name of the class to load
        
    Returns:
        The strategy class
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Error loading strategy class: {str(e)}")
        raise

def parse_params(params_str: str) -> Dict[str, Any]:
    """
    Parse parameters from a string, handling various formats.
    
    Args:
        params_str: Parameters as a string
        
    Returns:
        Dictionary of parameters
    """
    # Try to parse as JSON
    try:
        return json.loads(params_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to parse as a simple key-value string
        try:
            # Handle format like: key1=value1,key2=value2
            if '=' in params_str and ',' in params_str:
                result = {}
                for pair in params_str.split(','):
                    key, value = pair.split('=')
                    # Try to convert value to appropriate type
                    try:
                        # Try to convert to float first
                        value = float(value)
                        # If it's an integer, convert to int
                        if value.is_integer():
                            value = int(value)
                    except ValueError:
                        # If conversion fails, keep as string
                        pass
                    result[key.strip()] = value
                return result
            
            # Handle format like: key1:value1 key2:value2
            elif ':' in params_str:
                result = {}
                for pair in params_str.split():
                    key, value = pair.split(':')
                    # Try to convert value to appropriate type
                    try:
                        # Try to convert to float first
                        value = float(value)
                        # If it's an integer, convert to int
                        if value.is_integer():
                            value = int(value)
                    except ValueError:
                        # If conversion fails, keep as string
                        pass
                    result[key.strip()] = value
                return result
        except Exception as e:
            logger.error(f"Error parsing parameters: {str(e)}")
            raise ValueError(f"Could not parse parameters: {params_str}. Error: {str(e)}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run a backtest with any strategy')
    parser.add_argument('--strategy', type=str, required=True, 
                        help='Strategy module path (e.g., strategy.ta_strategy)')
    parser.add_argument('--class', type=str, required=True, dest='class_name',
                        help='Strategy class name (e.g., TAIndicatorStrategy)')
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='Trading symbol (default: AAPL)')
    parser.add_argument('--start', type=str, default='2020-01-01',
                        help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000.0,
                        help='Initial capital for backtest')
    parser.add_argument('--params', type=str, default='{}',
                        help='Strategy parameters as JSON string or key=value pairs')
    parser.add_argument('--params-file', type=str,
                        help='Path to JSON file containing strategy parameters')
    parser.add_argument('--no-plot', action='store_true',
                        help='Do not plot results')
    parser.add_argument('--no-save', action='store_true',
                        help='Do not save plot to file')
    
    args = parser.parse_args()
    
    # Load strategy class
    strategy_class = load_strategy_class(args.strategy, args.class_name)
    
    # Parse strategy parameters
    if args.params_file:
        # Load parameters from file
        if os.path.exists(args.params_file):
            with open(args.params_file, 'r') as f:
                strategy_params = json.load(f)
        else:
            raise FileNotFoundError(f"Parameters file not found: {args.params_file}")
    else:
        # Parse parameters from command line
        strategy_params = parse_params(args.params)
    
    # Create backtester
    backtester = Backtester(strategy_class, strategy_params)
    
    # Run backtest
    backtester.run(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        plot_results=not args.no_plot,
        save_plot=not args.no_save
    )

if __name__ == "__main__":
    main() 