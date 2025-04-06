# Quantitative Trading System

A robust quantitative trading system that identifies stocks primed for trading strategies and analyzes them during market hours.

## Features

- **Market Ticker Query**: Analyzes stocks in pre/post markets and last trading day to identify stocks primed for quantitative trading strategies.
- **Open Market Loader**: Analyzes the identified stocks during market hours and generates trading signals after 10:15 AM Eastern time.
- **Technical Analysis**: Uses multiple technical indicators to generate trading signals.
- **Real-time Data Collection**: Collects and analyzes real-time market data using Alpaca's API.
- **Configurable Parameters**: Easily adjust parameters to customize the analysis.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quant_trading.git
cd quant_trading
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Alpaca API credentials:
   - Create a `.env` file in the root directory with the following content:
   ```
   ALPACA_API_KEY_ID=your_api_key_id
   ALPACA_SECRET_KEY=your_secret_key
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```
   - Replace `your_api_key_id` and `your_secret_key` with your actual Alpaca API credentials.

## Usage

### Running the Market Analysis

To run the complete market analysis system:

```bash
python src/run_market_analysis.py
```

This will:
1. Run the market ticker query to identify stocks primed for trading
2. Run the open market loader to analyze the identified stocks during market hours

### Command Line Options

The `run_market_analysis.py` script supports the following command line options:

- `--mode`: Mode to run: `query` (market ticker query), `loader` (open market loader), or `both` (default)
- `--max-symbols`: Maximum number of symbols to analyze (default: 100)
- `--wait`: Wait for market to open if it is closed

Example:
```bash
python src/run_market_analysis.py --mode query --max-symbols 50 --wait
```

### Running Individual Components

You can also run the individual components separately:

#### Market Ticker Query

```bash
python src/market_ticker_query.py
```

This will analyze the market and identify stocks primed for trading.

#### Open Market Loader

```bash
python src/open_market_loader.py
```

This will analyze the identified stocks during market hours and generate trading signals.

## Configuration

The system can be configured by modifying the parameters in the following files:

- `src/market_ticker_query.py`: Configure the market ticker query parameters
- `src/open_market_loader.py`: Configure the open market loader parameters

## Directory Structure

- `src/`: Source code
  - `market_ticker_query.py`: Market ticker query module
  - `open_market_loader.py`: Open market loader module
  - `run_market_analysis.py`: Script to run the complete market analysis
- `data/`: Data directory
  - `market_analysis/`: Market analysis results
  - `trading_signals/`: Trading signals
  - `cache/`: Cached data

## Logging

The system logs information to the following files:

- `market_ticker_query.log`: Logs from the market ticker query
- `open_market_loader.log`: Logs from the open market loader
- `market_analysis.log`: Logs from the run market analysis script

## Data Sources

The system uses Alpaca's API to fetch market data, including:
- Pre-market and post-market data
- Intraday data for technical analysis
- Historical data for backtesting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
