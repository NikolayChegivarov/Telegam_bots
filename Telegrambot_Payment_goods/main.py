from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio

from config import Config
from handlers import common, client, admin, payment
from database import check_and_create_db, initialize_database

async def main():
    # Инициализировать бота и диспетчера
    bot = Bot(
        token=Config.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Проверка соединения и наличия, создание базы данных.
    check_and_create_db()
    initialize_database()

    # Включить маршрутизаторы
    dp.include_router(common.router)
    dp.include_router(client.router)
    dp.include_router(admin.router)
    dp.include_router(payment.router)

    # Начать запросы
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())