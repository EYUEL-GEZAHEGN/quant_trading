from db.utils import init_db
init_db()

import argparse
from src.backtest.engine import run_backtest
from src.live_trading.executor import run_live_trading
from src.strategy.mean_reversion import MeanReversionBot
from src.strategy.breakout import BreakoutBot
from src.strategy.stat_arb import StatArbBot
from src.strategy.sentiment_strategy import SentimentBot
from src.strategy.ta_strategy import TAIndicatorStrategy
from src.strategy.mixed_signal import MixedSignalsStrategy


strategies = {
    'mean_reversion': MeanReversionBot,
    'breakout': BreakoutBot,
    'stat_arb': StatArbBot,  # special handling below
    'sentiment': SentimentBot,
    'mean_reversion': MeanReversionBot,
    'ta_indicator': TAIndicatorStrategy,
    'mixed_signals': MixedSignalsStrategy
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['live', 'paper', 'backtest'], required=True)
    parser.add_argument('--strategy', required=True)
    parser.add_argument('--symbol', required=True)
    parser.add_argument('--pair', type=str, help='Second symbol for pair strategy (like stat_arb)')
    parser.add_argument('--start', type=str, help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='Backtest end date (YYYY-MM-DD)')
    args = parser.parse_args()

    if args.strategy == 'stat_arb':
        if not args.pair:
            print("Statistical Arbitrage strategy requires --pair argument.")
            return
        Strategy = lambda symbol: StatArbBot(symbol, args.pair)
    else:
        Strategy = strategies.get(args.strategy)
        if not Strategy:
            print("Invalid strategy name.")
            return

    if args.mode == 'backtest':
        run_backtest(Strategy, args.symbol, args.start, args.end)
    else:
        run_live_trading(Strategy, args.symbol, live=(args.mode == 'live'))

#python main.py --mode paper --strategy ta_indicator --symbol TQQQ


if __name__ == "__main__":
    main()
