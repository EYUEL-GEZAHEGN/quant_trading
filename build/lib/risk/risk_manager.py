# Risk checks, stop-loss, exposure limits



# risk_manager.py

class RiskManager:
    def __init__(self, portfolio_value=100.0, max_risk_pct=0.002):
        """
        Initializes the RiskManager.

        :param portfolio_value: Total value of the portfolio in dollars
        :param max_risk_pct: Max risk per trade as a decimal (e.g., 0.002 = 0.2%)
        """
        self.portfolio_value = portfolio_value
        self.max_risk_pct = max_risk_pct

    def update_portfolio_value(self, new_value):
        self.portfolio_value = new_value

    def get_max_allocation(self):
        return self.portfolio_value * self.max_risk_pct

    def calculate_qty(self, price):
        """Returns fractional quantity based on max allocation and current price."""
        allocation = self.get_max_allocation()
        if price == 0:
            return 0
        return round(allocation / price, 6)

    def validate(self, signal):
        """
        Placeholder method for signal validation logic.
        Could include checks like max exposure per ticker, stop-loss thresholds, etc.
        """
        return True
