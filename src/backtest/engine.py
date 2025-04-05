from src.data_loader import load_data, load_pair_data
import matplotlib.pyplot as plt

def run_backtest(StrategyClass, symbol, start_date, end_date):
    # Instantiate strategy
    strategy = StrategyClass(symbol)

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
        signals['zscore'].plot(title="Z-Score")
    else:
        signals['signal'].plot(title="Trading Signals")
    plt.show()
