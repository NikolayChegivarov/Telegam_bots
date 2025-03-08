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
    await dp.start_polling(bot, handler_signals=False)  # Слушает сервера телеграм, не пришло ли на адрес бота сообщение.

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"\nПроизошла ошибка: {str(e)}")
