import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os
import database
from middleware import AuthMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(  # Основной класс aiogram для работы с Telegram Bot API.
    token=os.getenv("TELEGRAM_TOKEN_BOT"),  # Загрузка токена бота из переменных окружения.
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Сообщения будут обрабатываться как HTML.
)
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

# Регистрация обработчиков
register_common_handlers(dp)
register_client_handlers(dp)
register_master_handlers(dp)
register_admin_handlers(dp)


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
