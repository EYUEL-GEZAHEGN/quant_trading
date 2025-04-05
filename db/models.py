# SQLAlchemy models for trades, performance, etc.


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime

# Base class for SQLAlchemy models
Base = declarative_base()

# Trade table
class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    symbol = Column(String)               # e.g., AAPL
    side = Column(String)                 # buy or sell
    qty = Column(Float)                   # quantity of shares
    price = Column(Float)                 # price per share
    timestamp = Column(DateTime, default=datetime.utcnow)  # time of execution
    strategy = Column(String)             # strategy name (e.g., MeanReversionBot)
    mode = Column(String)                 # live, paper, stop_loss, take_profit, etc.
