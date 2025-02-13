from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()


def connect_to_database():
    """Функция устанавливает подключение к базе данных PostgreSQL."""
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("NAME_DB"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD_DB"),
            port=os.getenv("PORT")
        )
        print(f"Подключение к PostgreSQL успешно установлено: {connection}")
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при подключении к PostgreSQL: {error}")
        return None
