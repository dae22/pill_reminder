import asyncio
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import *
from database import database, init_db
from handlers import common, pills

async def main():
    await database.connect()
    await init_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(pills.router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(pills.check_pills, 'interval', minutes=1, args=[bot])
    scheduler.start()

    try:
        await dp.start_polling(bot)
    finally:
        await database.disconnect()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())