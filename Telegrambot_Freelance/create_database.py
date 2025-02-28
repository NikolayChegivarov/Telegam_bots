from dotenv import load_dotenv, find_dotenv
import psycopg2
from psycopg2 import sql
import os

load_dotenv()


def connect_to_database(dbname=None):
    """Функция устанавливает подключение к базе данных PostgreSQL."""
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=dbname if dbname else os.getenv("NAME_DB"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD_DB"),
            port=os.getenv("PORT")
        )
        # print(f"Подключение к PostgreSQL успешно установлено: {connection}")
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при подключении к PostgreSQL: {error}")
        return None


def check_db_connection():
    """Проверка соединения с PostgreSQL."""
    connection = connect_to_database(dbname="postgres")  # Подключение к стандартной базе данных
    if connection:
        connection.close()
        print("Соединение с PostgreSQL успешно проверено.")
        return True
    return False


def check_and_create_db():
    """Проверка наличия базы данных и её создание, если она отсутствует."""
    connection = connect_to_database(dbname="postgres")  # Подключение к стандартной базе данных
    if not connection:
        return

    try:
        connection.autocommit = True
        cursor = connection.cursor()

        # Проверка наличия базы данных
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [os.getenv("NAME_DB")])
        exists = cursor.fetchone()

        if not exists:
            # Создание базы данных, если она отсутствует
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(os.getenv("NAME_DB"))))
            print(f"База данных {os.getenv('NAME_DB')} успешно создана.")
        else:
            print(f"База данных {os.getenv('NAME_DB')} уже существует.")

        cursor.close()
    except Exception as e:
        print(f"Ошибка при проверке или создании базы данных: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    if check_db_connection():
        check_and_create_db()
