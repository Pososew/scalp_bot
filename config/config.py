from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
ALLOWED_USERS = [int(user_id) for user_id in os.getenv("ALLOWED_USERS").split(",")]

SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
    "ADA/USDT",
    "XRP/USDT",
    "DOGE/USDT",
    "AVAX/USDT",
    "DOT/USDT",
    "LINK/USDT"
]
AMOUNT_USD = 50
PROFIT_TARGET = 0.003
STOP_LOSS = 0.005
TIMEFRAME = '1m'