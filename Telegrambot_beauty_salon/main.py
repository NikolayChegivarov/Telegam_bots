import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os
import database
from utils import notify_master_about_appointment

from middleware import AuthMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"), parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
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

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)