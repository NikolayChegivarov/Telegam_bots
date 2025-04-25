from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
from config import Config
from database import check_and_create_db, initialize_database
from handlers import admin, executor, common


async def main():
    try:
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
        dp.include_router(executor.router)
        dp.include_router(admin.router)

        # Начать запросы
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        print("\nРабота бота завершена пользователем")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nРабота бота завершена пользователем")