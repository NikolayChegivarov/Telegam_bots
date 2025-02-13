"""
Данный модуль реструктурирует наш код, чтобы решить проблему
циклического импорта путем помещения сюда общих функций.
"""

from telebot import TeleBot
from dotenv import load_dotenv
import os
from database_connection import connect_to_database
from activ_db_check import activ_check
from connection_check import check_database_connection

load_dotenv()

TELEGRAM_TOKEN_BOT = os.getenv("TELEGRAM_TOKEN_BOT")


def create_bot():
    """
    Создает экземпляр бота Telegram.

    Возвращает: TeleBot - объект бота Telegram.
    """
    return TeleBot(TELEGRAM_TOKEN_BOT)


def get_db_connection():
    """
    Устанавливает соединение с базой данных и проверяет его активность.

    Возвращает: tuple - кортеж из соединения (cnx) и курсора (cursor), если подключение успешно установлено.
    Вызывает исключение ConnectionError, если не удается установить соединение.
    """
    cnx = connect_to_database()
    if check_database_connection(cnx):
        cursor = cnx.cursor()
        activ_check(cursor)
        return cnx, cursor
    else:
        raise ConnectionError("Failed to establish database connection")


