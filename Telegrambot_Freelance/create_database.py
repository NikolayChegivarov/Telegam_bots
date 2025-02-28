from dotenv import load_dotenv, find_dotenv
import psycopg2
from psycopg2 import sql
import os

load_dotenv()
# Загрузка переменных окружения
TELEGRAM_TOKEN_BOT = os.getenv('TELEGRAM_TOKEN_BOT')
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PASSWORD_DB = os.getenv('PASSWORD_DB')
PORT = os.getenv('PORT')
NAME_DB = os.getenv('NAME_DB', 'Telegrambot_Freelance')
print(PASSWORD_DB)
print(USER)


def check_db_connection():
    """Проверяем есть ли подключение к postgres."""
    try:
        # Попытка подключения к стандартной базе данных.
        conn = psycopg2.connect(
            host=HOST,
            user=USER,
            password=PASSWORD_DB,
            port=PORT,
            dbname="postgres"  # Стандартная бд postgres.
        )
        conn.close()
        print("Соединение с PostgreSQL успешно установлено.")
        return True
    except Exception as e:
        print(f"Ошибка при подключении к PostgreSQL: {e}")
        return False


def check_and_create_db():
    """Если есть подключение проверяем наличие нашей бд.
    Если бд нет, создаем ее.
    """

    try:
        # Подключение к стандартной базе данных для проверки наличия целевой базы данных.
        conn = psycopg2.connect(
            host=HOST,
            user=USER,
            password=PASSWORD_DB,
            port=PORT,
            dbname="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Проверка наличия базы данных
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [NAME_DB])
        exists = cursor.fetchone()

        if not exists:
            # Создание базы данных, если она отсутствует
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(NAME_DB)))
            print(f"База данных {NAME_DB} успешно создана.")
        else:
            print(f"База данных {NAME_DB} уже существует.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при проверке или создании базы данных: {e}")


if __name__ == "__main__":
    if check_db_connection():
        check_and_create_db()
