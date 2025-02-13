import mysql.connector
import telebot
from slavin_config import *

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def connect_to_database():
    """Функция устанавливает подключение к базе данных. """
    cnx = mysql.connector.connect(
        host=your_host,
        user=your_user,
        password=your_password,
        port=your_port,
        database=your_database,
        connect_timeout=300  # Установка таймаута подключения.
    )
    print(f'Создаем объект соединения MySQL {cnx}')
    cursor = cnx.cursor()
    return cnx, cursor


