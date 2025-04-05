# DB init and helper functions

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Trade
from datetime import datetime

# SQLite file location
DATABASE_URL = "sqlite:///db/trading.db"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def init_db():
    Base.metadata.create_all(engine)

def log_trade(symbol, side, qty, price, strategy, mode):
    trade = Trade(
        symbol=symbol,
        side=side,
        qty=qty,
        price=price,
        strategy=strategy,
        mode=mode,
        timestamp=datetime.utcnow()
    )
    session.add(trade)
    session.commit()
