from aiogram.fsm.storage.memory import MemoryStorage
from middleware import AuthMiddleware
from aiogram import Dispatcher
import logging
import asyncio
import database
from bot_instance import bot
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()


# Хранилище состояний FSM. Временные данные (например, состояние диалога с пользователем) в оперативной памяти.
storage = MemoryStorage()
# Создание диспетчера. Dispatcher - центральный компонент aiogram, который: Обрабатывает входящие updates от Telegram;
# Перенаправляет их соответствующим обработчикам Router(ам); Управляет FSM (машиной состояний).
# bot=bot - привязка созданного экземпляра бота, storage=storage - использование созданного хранилища.
dp = Dispatcher(bot=bot, storage=storage)
# Аутентификации пользователей, логирования, проверки прав доступа.
dp.message.middleware(AuthMiddleware())

# Инициализация базы данных
database.check_and_create_db()
database.initialize_database()

# Импорт обработчиков
from handlers.common_handlers import register_common_handlers
from handlers.client_handlers import register_client_handlers
from handlers.master_handlers import register_master_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.payments_handlers import register_payment_handlers

# Регистрация обработчиков
register_common_handlers(dp)
register_client_handlers(dp)
register_master_handlers(dp)
register_admin_handlers(dp)
register_payment_handlers(dp)


async def on_startup():
    logger.info("Бот запущен")


async def on_shutdown():
    logger.info("Завершение работы бота...")
    await bot.session.close()
    logger.info("Бот успешно остановлен")


async def main():
    await on_startup()
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await on_shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
