import numpy as np
import pandas as pd

class MonteCarlo:
    def __init__(self, df, price_col='close', T=1, steps=252, simulations=1000):
        """
        df: DataFrame with historical prices
        price_col: column name of price (e.g. 'close')
        T: time horizon in years
        steps: number of steps (252 = daily, 12 = monthly, etc.)
        simulations: number of paths to simulate
        """
        self.df = df
        self.price_col = price_col
        self.T = T
        self.N = steps
        self.M = simulations
        self.dt = T / steps

        # Compute daily log returns
        self.df['log_return'] = np.log(self.df[price_col] / self.df[price_col].shift(1))
        self.mu = self.df['log_return'].mean() * steps
        self.sigma = self.df['log_return'].std() * np.sqrt(steps)
        self.S0 = self.df[price_col].iloc[-1]

    def generate_paths(self):
        """
        Run Monte Carlo simulations
        """
        paths = np.zeros((self.N + 1, self.M))
        paths[0] = self.S0

        for t in range(1, self.N + 1):
            z = np.random.standard_normal(self.M)
            paths[t] = paths[t - 1] * np.exp(
                (self.mu - 0.5 * self.sigma**2) * self.dt + self.sigma * np.sqrt(self.dt) * z
            )

        self.paths = paths
        self.ending_prices = paths[-1]
        return paths

    def value_at_risk(self, alpha=0.05):
        """
        Calculate Value at Risk (VaR) at given confidence level.
        VaR is the threshold loss not exceeded with 1 - alpha probability.
        """
        if not hasattr(self, 'ending_prices'):
            self.generate_paths()

        pct_loss = (self.S0 - self.ending_prices) / self.S0
        var = np.percentile(pct_loss, alpha * 100)
        return var

    def conditional_value_at_risk(self, alpha=0.05):
        """
        Calculate Conditional VaR (CVaR) — expected loss beyond the VaR.
        """
        if not hasattr(self, 'ending_prices'):
            self.generate_paths()

        pct_loss = (self.S0 - self.ending_prices) / self.S0
        var_threshold = np.percentile(pct_loss, alpha * 100)
        cvar = pct_loss[pct_loss >= var_threshold].mean()
        return cvar
