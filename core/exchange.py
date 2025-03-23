import ccxt
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
import pandas as pd

exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'options': {'defaultType': 'future'}
})

def get_current_price(symbol):
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

def fetch_ohlcv(symbol, timeframe='1m', limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    return df
