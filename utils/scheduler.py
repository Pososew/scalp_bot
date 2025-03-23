from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram_bot.handlers import auto_signals_check

scheduler = AsyncIOScheduler()

def start_scheduler(application):
    scheduler.add_job(auto_signals_check, "interval", minutes=5, args=[application])
    scheduler.start()
