import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, accounts, templates, campaigns, yandex, admin, common, payment
from database import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    await init_db()
    dp.include_router(start.router)
    dp.include_router(accounts.router)
    dp.include_router(templates.router)
    dp.include_router(campaigns.router)
    dp.include_router(yandex.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(payment.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())