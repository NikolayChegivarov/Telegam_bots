from datetime import datetime

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_database(dbname=None):
    """Функция устанавливает подключение к базе данных указанной в аргументе."""
    if dbname is None:
        dbname = os.getenv("NAME_DB")
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=dbname if dbname else os.getenv("NAME_DB"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD_DB"),
            port=os.getenv("PORT")
        )
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при подключении к PostgreSQL: {error}")
        return None

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
        return True
    except Exception as e:
        print(f"Ошибка при проверке или создании базы данных: {e}")
    finally:
        connection.close()

def initialize_database():
    """Функция для инициализации базы данных, включая создание таблиц, если они отсутствуют."""
    connection = connect_to_database()
    if not connection:
        return

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS My_services (
                id_services BIGINT PRIMARY KEY,
                description VARCHAR(200),
                Amount NUMERIC(10, 2) NOT NULL,
                payment_status VARCHAR(30) NOT NULL 
                    CHECK (payment_status IN ('Оплачен', 'Не оплачен')),
                client VARCHAR(50) NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP NULL
            )
        """)

        connection.commit()
        print("Таблица My_services успешно создана или уже существует.")

    except Exception as e:
        connection.rollback()
        print(f"Ошибка при создании таблицы: {e}")
    finally:
        cursor.close()
        connection.close()

def create_service(description, amount):
    """Создать новую услугу"""
    connection = connect_to_database()
    if not connection:
        return None

    try:
        cursor = connection.cursor()
        service_id = int(datetime.now().timestamp())
        cursor.execute(
            "INSERT INTO My_services (id_services, description, Amount, payment_status, client) VALUES (%s, %s, %s, %s, %s)",
            (service_id, description, amount, 'Не оплачен', '')
        )
        connection.commit()
        return service_id
    except Exception as e:
        print(f"Error creating service: {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()

def get_service_by_id(service_id):
    """Получить услугу по ID"""
    connection = connect_to_database()
    if not connection:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM My_services WHERE id_services = %s", (service_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error getting service: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def update_service_description(service_id, new_description):
    """Обновить описание услуги"""
    connection = connect_to_database()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE My_services SET description = %s WHERE id_services = %s",
            (new_description, service_id)
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating service description: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def update_service_amount(service_id, new_amount):
    """Обновить стоимость услуги"""
    connection = connect_to_database()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE My_services SET Amount = %s WHERE id_services = %s",
            (new_amount, service_id)
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating service amount: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def update_service(service_id, new_description, new_amount):
    """Обновить описание и стоимость услуги"""
    connection = connect_to_database()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE My_services SET description = %s, Amount = %s WHERE id_services = %s",
            (new_description, new_amount, service_id)
        )
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating service: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def status_service(service_id):
    """Получить статус услуги по ID"""
    connection = connect_to_database()
    if not connection:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT payment_status FROM My_services WHERE id_services = %s", (service_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting service status: {e}")
        return None
    finally:
        cursor.close()
        connection.close()