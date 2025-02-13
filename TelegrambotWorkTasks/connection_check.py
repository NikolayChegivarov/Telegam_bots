from psycopg2 import OperationalError
import psycopg2
import os


def get_db_connection():
    try:
        connection_params = {
            'dbname': 'your_database',
            'user': 'your_user',
            'password': 'your_password',
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }

        connection = psycopg2.connect(**connection_params)
        return connection, connection.cursor()

    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None, None


def check_database_connection(db_connection):
    """
    Проверяет подключение к базе данных.

    Args:
    db_connection (psycopg2 connection): Объект соединения с базой данных.

    Returns:
    bool: True, если подключение установлено успешно; False в противном случае.

    Raises:
    OperationalError: При возникновении ошибок операционной работы с базой данных.
    """
    if db_connection is None:
        return False

    try:
        cursor = db_connection.cursor()
        cursor.execute("SELECT 1")
        print("Подключение к базе данных установлено.")
        return True
    except OperationalError:
        print("Не удалось подключиться к базе данных.")
        return False
