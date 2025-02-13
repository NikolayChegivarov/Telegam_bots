from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import datetime
import logging
from dotenv import load_dotenv
import os


load_dotenv()

telegram_token = os.getenv('TELEGRAM_TOKEN')

# Включите логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция для обработки сообщений
async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    print(f"user_message: {user_message}")
    user_id = update.message.chat_id
    now = datetime.datetime.now()

    # Проверяем, выходной ли день (суббота или воскресенье)
    if now.weekday() >= 5:  # 5 - суббота, 6 - воскресенье
        await context.bot.send_message(chat_id=user_id, text="Сегодня выходной день. Мы ответим вам в ближайший рабочий день.")
    # Проверяем, будний день и время после 17:00
    elif now.weekday() < 5 and now.hour >= 17:
        await context.bot.send_message(chat_id=user_id, text="Рабочий день закончился. Извините, ответим завтра.")
    else:
        await context.bot.send_message(chat_id=user_id, text="Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.")


# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Привет! Напишите мне что-нибудь, и я отвечу.')


# Функция для обработки ошибок
async def error(update: Update, context: CallbackContext):
    logger.warning(f'Update {update} caused error {context.error}')


# Основная функция
def main():
    # Вставьте сюда ваш токен
    token = telegram_token

    # Создаем Application и передаем ему токен вашего бота
    application = Application.builder().token(token).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))

    # Регистрируем обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error)

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()
