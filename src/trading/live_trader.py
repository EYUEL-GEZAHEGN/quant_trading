import os
import time
import logging
from datetime import datetime
import pytz
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from risk.MonteCarlo import MonteCarlo  # New import
from risk.risk_manager import RiskManager

class LiveTrader:
    def __init__(self, strategy, symbol, interval='5m', max_cvar_threshold=0.05):
        """
        Initialize the live trader.
        
        Args:
            strategy: Trading strategy instance
            symbol: Trading symbol (e.g., 'AAPL')
            interval: Trading interval ('1m', '5m', '15m', '1h', '1D')
            max_cvar_threshold: Maximum allowed Conditional Value at Risk (CVaR)
        """
        self.strategy = strategy
        self.symbol = symbol
        self.interval = interval
        self.max_cvar_threshold = max_cvar_threshold
        self.logger = logging.getLogger(__name__)
        self.risk_manager = RiskManager(portfolio_value=100, max_risk_pct=0.002)

        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=os.getenv('ALPACA_API_KEY_ID'),
            secret_key=os.getenv('ALPACA_API_SECRET_KEY'),
            paper=True
        )

        self.data_client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY_ID'),
            secret_key=os.getenv('ALPACA_API_SECRET_KEY')
        )

        self.timezone = pytz.timezone('US/Eastern')
        self.position = None
        self.last_signal = 0

    def _get_timeframe(self):
        timeframe_map = {
            '1m': TimeFrame.Minute,
            '5m': TimeFrame.Minute,
            '15m': TimeFrame.Minute,
            '1h': TimeFrame.Hour,
            '1D': TimeFrame.Day
        }
        return timeframe_map.get(self.interval, TimeFrame.Day)

    def _get_market_data(self):
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=self.symbol,
                timeframe=self._get_timeframe(),
                start=datetime.now(self.timezone).date(),
                end=datetime.now(self.timezone).date()
            )
            bars = self.data_client.get_stock_bars(request_params)
            return bars.df
        except Exception as e:
            self.logger.error(f"Error fetching market data: {str(e)}")
            return None

    def _execute_trade(self, signal, current_price):
        try:
            qty = self.risk_manager.calculate_qty(current_price)

            # Refresh position
            positions = self.trading_client.get_all_positions()
            self.position = next((p for p in positions if p.symbol == self.symbol), None)

            if signal == 2 and self.last_signal != 2:
                if self.position and self.position.side == 'short':
                    self.trading_client.close_position(self.symbol)

                self.trading_client.submit_order(
                    symbol=self.symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
                self.logger.info(f"Opened long position for {self.symbol} with {qty} shares")

            elif signal == 1 and self.last_signal != 1:
                if self.position and self.position.side == 'long':
                    self.trading_client.close_position(self.symbol)

                self.trading_client.submit_order(
                    symbol=self.symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='day'
                )
                self.logger.info(f"Opened short position for {self.symbol} with {qty} shares")

            elif signal == 0 and self.last_signal != 0:
                if self.position:
                    self.trading_client.close_position(self.symbol)
                    self.logger.info(f"Closed position for {self.symbol}")

            self.last_signal = signal

        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")


    def _risk_management_check(self, df):
        mc = MonteCarlo(df['close'].values)
        var, cvar = mc.value_at_risk(), mc.conditional_value_at_risk()
        self.logger.info(f"VaR: {var:.4f}, CVaR: {cvar:.4f}")
        return cvar <= self.max_cvar_threshold

    def start(self):
        self.logger.info(f"Starting live trading for {self.symbol}")

        while True:
            try:
                clock = self.trading_client.get_clock()
                if not clock.is_open:
                    self.logger.info("Market is closed. Waiting...")
                    time.sleep(60)
                    continue

                data = self._get_market_data()
                if data is None or data.empty:
                    self.logger.warning("No market data available")
                    time.sleep(60)
                    continue

                if not self._risk_management_check(data):
                    self.logger.warning("Risk too high. Skipping trade.")
                    time.sleep(60)
                    continue

                signals = self.strategy.generate_signals(data)
                if signals is None or signals.empty:
                    self.logger.warning("No signals generated")
                    time.sleep(60)
                    continue

                latest_signal = signals['signal'].iloc[-1]
                current_price = data['close'].iloc[-1]
                self._execute_trade(latest_signal)

                time.sleep(60)

            except KeyboardInterrupt:
                self.logger.info("Trading stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in trading loop: {str(e)}")
                time.sleep(60)
