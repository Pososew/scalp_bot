from telegram.ext import Application
from config.config import TELEGRAM_BOT_TOKEN
from telegram_bot.handlers import setup_handlers
from utils.scheduler import start_scheduler

async def post_init(application):
    start_scheduler(application)

def run_bot():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    setup_handlers(app)
    print("Telegram Bot started!")

    app.post_init = post_init  # <-- теперь это асинхронная функция

    app.run_polling()
