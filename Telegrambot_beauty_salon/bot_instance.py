# Здесь находится инициализация бота, для удобного импорта в разные модули.
from aiogram import Bot
import os

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Инициализация бота
bot = Bot(  # Основной класс aiogram для работы с Telegram Bot API.
    token=os.getenv("TELEGRAM_TOKEN_BOT"),  # Загрузка токена бота из переменных окружения.
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Сообщения будут обрабатываться как HTML.
)
