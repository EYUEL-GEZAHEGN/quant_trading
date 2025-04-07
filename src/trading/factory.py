from src.strategy.ta_strategy import TAIndicatorStrategy
from src.strategy.mean_reversion import MeanReversionBot
from src.strategy.mixed_signal import MixedSignalsStrategy
from src.strategy.harris_candles import HarrisCandlesStrategy
from src.strategy.micro_strategy import MicroMomentum

class StrategyFactory:
    @staticmethod
    def create_strategy(strategy_name: str, symbol: str):
        """
        Create a strategy instance based on the strategy name.
        
        Args:
            strategy_name: Name of the strategy to create
            symbol: Trading symbol
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy name is not recognized
        """
        strategy_map = {
            'ta_indicator': TAIndicatorStrategy,
            'mean_reversion': MeanReversionBot,
            'mixed_signal': MixedSignalsStrategy,
            'harris_candles': HarrisCandlesStrategy,
            'micro_momentum': MicroMomentum
        }
        
        strategy_class = strategy_map.get(strategy_name)
        if strategy_class is None:
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
        return strategy_class(symbol) 