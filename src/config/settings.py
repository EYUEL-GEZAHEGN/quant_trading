import os
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY_ID")
ALPACA_API_SECRET = os.getenv("ALPACA_SECRET_KEY")
PAPER_TRADING = True # toggle for live/paper


#USE THIS FOR LIVE-TRADING 
# BASE_URL = "https://paper-api.alpaca.markets"


