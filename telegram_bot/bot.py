from telegram.ext import Application
from config.config import TELEGRAM_BOT_TOKEN
from telegram_bot.handlers import setup_handlers

def run_bot():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    setup_handlers(app)
    print("Telegram Bot started!")
    app.run_polling()
