import pandas as pd
from abc import ABC, abstractmethod

class Strategy(ABC):
    def __init__(self, symbol):
        self.symbol = symbol

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        pass
