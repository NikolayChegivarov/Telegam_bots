import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import router

# Загрузка переменных окружения
import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)  # Слушает сервера телеграм, не пришло ли на адрес бота сообщение.

if __name__ == '__main__':
    asyncio.run(main())