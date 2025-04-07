from src.data_loader import load_data, load_pair_data
import matplotlib.pyplot as plt

def run_backtest(strategy, symbol, start_date, end_date):
    """Run backtest for a given strategy and symbol."""
    # Load data for single or pair strategy
    if strategy.__class__.__name__ == "StatArbBot":
        data = load_pair_data(symbol, strategy.pair_symbol, start_date, end_date)
    else:
        data = load_data(symbol, start_date, end_date)

    signals = strategy.generate_signals(data)
    print("\n🧠 Signal Value Counts:")
    print(signals['signal'].value_counts(dropna=False).sort_index())
    print("\n📄 Preview of Signals:")
    print(signals[['signal']].tail(10))

    # Determine which price column to use
    if strategy.__class__.__name__ == "StatArbBot":
        price_col = symbol  # e.g., "TQQQ"
    else:
        price_col = "close"

    # Initialize portfolio
    position = 0
    cash = 10000
    shares = 0

    for i in range(1, len(signals)):
        signal = signals['signal'].iloc[i]
        price = signals[price_col].iloc[i]

        if signal == 1 and position == 0:
            shares = cash // price
            cash -= shares * price
            position = 1
        elif signal == -1 and position == 1:
            cash += shares * price
            shares = 0
            position = 0

    final_value = cash + shares * signals[price_col].iloc[-1]
    print(f"\n📊 Final portfolio value: ${final_value:.2f}")
    print(f"📈 Return: {((final_value - 10000) / 10000) * 100:.2f}%")

    # Optional plot
    if 'zscore' in signals.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(signals.index, signals['zscore'], label='Z-Score')
        plt.axhline(y=1.5, color='r', linestyle='--', label='Upper Band')
        plt.axhline(y=-1.5, color='g', linestyle='--', label='Lower Band')
        plt.title(f'{symbol} Z-Score')
        plt.legend()
        plt.show()

    return {
        'symbol': symbol,
        'return': (final_value - 10000) / 10000,
        'sharpe_ratio': 0.0,  # TODO: Calculate Sharpe ratio
        'max_drawdown': 0.0   # TODO: Calculate max drawdown
    }
