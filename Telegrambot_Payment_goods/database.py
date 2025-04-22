from datetime import datetime
import psycopg2
from psycopg2 import sql
import os
# from dotenv import load_dotenv
from config import Config

# load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        port=Config.DB_PORT
    )


def connect_to_database(dbname=None):
    """Функция устанавливает подключение к базе данных указанной в аргументе."""
    if dbname is not None:
        # Если указано конкретное имя БД, используем его
        Config.DB_NAME = dbname
    try:
        connection = get_connection()
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при подключении к PostgreSQL: {error}")
        return None

def check_and_create_db():
    """Проверка наличия базы данных и её создание, если она отсутствует."""
    connection = None
    cursor = None
    try:
        connection = connect_to_database(dbname="postgres")  # Подключение к стандартной базе данных
        if not connection:
            return False

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

        return True
    except Exception as e:
        print(f"Ошибка при проверке или создании базы данных: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def initialize_database():
    """Функция для инициализации базы данных, включая создание таблиц, если они отсутствуют."""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return False

        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS My_services (
                id_services BIGINT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                description VARCHAR(200) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                client VARCHAR(50) NULL,
                status_services VARCHAR(30) NOT NULL 
                    DEFAULT 'Не сделано'
                    CHECK (status_services IN ('Сделано', 'Не сделано')),
                performed_at TIMESTAMP NULL,                   
                payment_status VARCHAR(30) NOT NULL 
                    DEFAULT 'Не оплачен'
                    CHECK (payment_status IN ('Оплачен', 'Не оплачен')),
                paid_at TIMESTAMP NULL
            )
        """)

        connection.commit()
        print("Таблица My_services успешно создана или уже существует.")
        return True
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Ошибка при создании таблицы: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_service(description, amount):
    """Создать новую услугу"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return None

        cursor = connection.cursor()
        service_id = int(datetime.now().timestamp())
        cursor.execute(
            "INSERT INTO My_services (id_services, description, amount, payment_status, client, performed_at, paid_at) "
            "VALUES (%s, %s, %s, %s, %s, NULL, NULL)",
            (service_id, description, amount, 'Не оплачен', '')
        )
        connection.commit()
        return service_id
    except Exception as e:
        print(f"Error creating service: {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_service_by_id(service_id):
    """Получить услугу по ID"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return None

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM My_services WHERE id_services = %s", (service_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error getting service: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_service_description(service_id, new_description):
    """Обновить описание услуги"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return False

        cursor = connection.cursor()
        cursor.execute(
            "UPDATE My_services SET description = %s WHERE id_services = %s",
            (new_description, service_id)
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating service description: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_service_amount(service_id, new_amount):
    """Обновить стоимость услуги"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return False

        cursor = connection.cursor()
        cursor.execute(
            "UPDATE My_services SET amount = %s WHERE id_services = %s",
            (new_amount, service_id)
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating service amount: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def update_service(service_id, new_description, new_amount):
    """Обновить описание и стоимость услуги"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return False

        cursor = connection.cursor()
        cursor.execute(
            "UPDATE My_services SET description = %s, amount = %s WHERE id_services = %s",
            (new_description, new_amount, service_id)
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating service: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def status_service(service_id):
    """Получить статус услуги по ID"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return None

        cursor = connection.cursor()
        cursor.execute("SELECT payment_status FROM My_services WHERE id_services = %s", (service_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting service status: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def update_payment_status(service_id, client_id):
    """Обновляет статус оплаты услуги в базе данных"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE My_services SET payment_status = 'Оплачен', "
                    "client = %s, paid_at = CURRENT_TIMESTAMP WHERE id_services = %s",
                    (client_id, service_id)
                )
        return True
    except Exception as e:
        print(f"Error updating payment status: {e}")
        return False


def update_service_status(service_id):
    """Обновляет статус выполнения услуги в базе данных"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE My_services SET status_services = 'Сделано', "
                    "performed_at = CURRENT_TIMESTAMP WHERE id_services = %s",
                    service_id
                )
        return True
    except Exception as e:
        print(f"Error updating payment status: {e}")
        return False
