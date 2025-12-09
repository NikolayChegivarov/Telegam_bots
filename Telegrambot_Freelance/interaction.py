# Взаимодействие.
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import TeleBot, types
from keyboard import Keyboards
import os
from dotenv import load_dotenv
load_dotenv()

# УБРАТЬ создание экземпляра бота здесь!
# bot = TeleBot(os.getenv("TELEGRAM_TOKEN_BOT"))

ADMIN = int(os.getenv("ADMIN"))
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


# Проверка доступа.
def access_check(bot, user_id):
    """Проверка доступа. Принять/Отклонить пользователя."""
    keyboard = Keyboards().access_check()
    # Отправляем ТОЛЬКО ID как текст, чтобы его легко было распарсить
    text = f"ID пользователя: {user_id}"
    bot.send_message(ADMIN, text=text, reply_markup=keyboard)


def request_organization(bot, user_id):
    """Выяснение типа клиента."""
    keyboard = Keyboards().registration_keyboard()
    bot.send_message(user_id, 'Вы являетесь физ лицом или организацией?', reply_markup=keyboard)


# Начальное сообщение менеджерам.
def client(bot, user_id):
    """Начальное меню клиенту. Просмотр задач/Поставить задачу.."""
    keyboard = Keyboards().client_keyboard()
    bot.send_message(user_id, text="Выберите действие:", reply_markup=keyboard)


def admin_menu(bot):
    """Меню исполнителя."""
    keyboard = Keyboards().admin_keyboard()
    bot.send_message(ADMIN, 'Выберите действие', reply_markup=keyboard)


def alter_status(bot, user_id, id_task):
    """Выбор статуса."""
    keyboard = Keyboards().alter_status()
    text = f"Выберите статус для задачи №{id_task}"
    bot.send_message(user_id, text, reply_markup=keyboard)


# Команда для создания платежа
def start_command(bot, chat_id_client):
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
