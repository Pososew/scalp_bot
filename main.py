from telegram_bot.bot import run_bot
from utils.scheduler import start_scheduler

if __name__ == "__main__":
    application = run_bot()
    start_scheduler(application)