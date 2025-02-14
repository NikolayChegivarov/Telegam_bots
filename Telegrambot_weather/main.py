import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import requests
import logging
import asyncio
import nest_asyncio

nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получаем токены из .env файла
TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

if not TOKEN or not WEATHER_API_KEY:
    logger.error("Отсутствуют токены в файле .env!")
    exit(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет! Я бот прогноза погоды.\n'
             'Введите название города, чтобы узнать погоду.'
    )


async def get_weather(city):
    """Получение данных о погоде"""
    base_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"

    try:
        response = requests.get(base_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        logger.error(f"Ошибка при получении данных погоды: {err}")
        return None


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений о погоде"""
    city = update.message.text.strip().lower()

    if not city:
        await update.message.reply_text("Пожалуйста, введите название города")
        return

    logger.info(f"Запрос погоды для города: {city}")
    weather_data = await get_weather(city)  # Добавили await

    if weather_data is None:
        await update.message.reply_text(
            f"Не удалось получить данные погоды для города '{city}'"
        )
        return

    current = weather_data['current']

    message = f"""
🌤️ Погода в городе {weather_data['location']['name']}:
Температура: {current['temp_c']}°C ({current['temp_f']}°F)
Ощущается как: {current['feelslike_c']}°C
Осадки: {current['precip_mm']} мм
Влажность: {current['humidity']}%
Ветер: {current['wind_kph']} км/ч
Направление ветра: {current['wind_dir']}
Условия: {current['condition']['text']}
"""

    await update.message.reply_text(message)


async def main():
    """Основная функция бота"""
    try:
        logger.info("Запуск бота...")
        application = ApplicationBuilder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather))

        logger.info("Бот запущен. Ожидание сообщений...")
        await application.run_polling()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == '__main__':
    try:
        logger.info("Запуск основной программы...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        exit(1)
