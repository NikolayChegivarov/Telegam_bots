from telebot import TeleBot, types
from keyboard import Keyboards
import os
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# from datetime import datetime
# import calendar

# Создание экземпляра бота
bot = TeleBot(os.getenv("TELEGRAM_TOKEN_BOT"))

ADMIN = int(os.getenv("ADMIN"))
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


# Проверка доступа.
@bot.message_handler(commands=['accept', 'reject'])
def access_check(user_id):
    """Проверка доступа. Принять/Отклонить пользователя."""
    keyboard = Keyboards().access_check()
    text = user_id
    bot.send_message(ADMIN, text=text, reply_markup=keyboard)


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


@bot.message_handler(commands=['tasks_all', 'status', 'del_task'])
def admin_menu():
    """Меню исполнителя."""
    keyboard = Keyboards().admin_keyboard()
    bot.send_message(ADMIN, 'Выберите действие', reply_markup=keyboard)


@bot.message_handler(commands=['work_task', 'to_mark', 'to_payment'])
def alter_status(user_id, id_task):
    """Выбор статуса."""
    keyboard = Keyboards().alter_status()
    text = f"Выберите статус для задачи №{id_task}"
    bot.send_message(user_id, text, reply_markup=keyboard)


# Команда для создания платежа
@bot.message_handler(commands=['to_payment'])
def start_command(chat_id_client):
    bot.send_message(chat_id_client, "Привет! Вот твой счет:")

    # Создаем инвойс (счет)
    prices = [
        types.LabeledPrice(label='Покупка товара', amount=1000)]  # Сумма в минимальных единицах (например, копейках)

    bot.send_invoice(
        chat_id=chat_id_client,
        title='Покупка товара',
        description='Описание товара',
        invoice_payload='some_payload',  # Уникальный идентификатор платежа
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency='RUB',  # Валюта
        prices=prices,
        start_parameter='start_parameter'
    )


# Обработка предварительного запроса оплаты
@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# Обработка успешного платежа
@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    bot.send_message(message.chat.id, "Оплата прошла успешно! Спасибо за покупку.")
