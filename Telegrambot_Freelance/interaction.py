from telebot import TeleBot
from keyboard import Keyboards
import os
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# from datetime import datetime
# import calendar

# Создание экземпляра бота
bot = TeleBot(os.getenv("TELEGRAM_TOKEN_BOT"))


# Проверка доступа.
@bot.message_handler(commands=['accept', 'reject'])
def access_check(user_id):
    """Проверка доступа. Принять/Отклонить пользователя."""
    keyboard = Keyboards().access_check()
    text = user_id
    bot.send_message(chat_id=os.getenv("ADMIN"), text=text, reply_markup=keyboard)


@bot.message_handler(commands=['natural_person', 'organization'])
def request_organization(user_id):
    """Выяснение типа клиента."""
    keyboard = Keyboards().registration_keyboard()
    bot.send_message(user_id, 'Вы являетесь физ лицом или организацией?', reply_markup=keyboard)


# Начальное сообщение менеджерам.
@bot.message_handler(commands=['tasks', 'set_a_task'])
def client(user_id):
    """Начальное меню клиенту. Просмотр задач/Поставить задачу.."""
    keyboard = Keyboards().client_keyboard()
    text = f"_________________\n       \nВыберите действие:"
    bot.send_message(user_id, text="Выберите действие:", reply_markup=keyboard)