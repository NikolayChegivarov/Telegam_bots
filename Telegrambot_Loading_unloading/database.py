import psycopg2
from psycopg2 import sql
import os

from config import Config

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
            CREATE TABLE IF NOT EXISTS users (
                id_users BIGINT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                is_loader BOOLEAN NOT NULL DEFAULT FALSE,        -- Грузчик (ДА/НЕТ)
                is_driver BOOLEAN NOT NULL DEFAULT FALSE,        -- Водитель (ДА/НЕТ)
                is_self_employed BOOLEAN NOT NULL DEFAULT FALSE, -- Самозанятый (ДА/НЕТ)
                inn VARCHAR(12) NULL,                            -- ИНН номер
                status VARCHAR(20) NOT NULL                      -- Статус (Активный/Заблокированный)
                    DEFAULT 'Активный'
                    CHECK (status IN ('Активный', 'Заблокированный')),
                comment TEXT NULL,                               -- Мой комментарий
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id_tasks BIGINT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Дата и время создания (автоматически)
                assignment_date DATE NULL,               -- Дата назначения
                assignment_time TIME NULL,               -- Время назначения
                task_type VARCHAR(20) NOT NULL           -- Тип задачи (Погрузка/Доставка)
                    CHECK (task_type IN ('Погрузка', 'Доставка')),
                description TEXT NOT NULL,               -- Описание задачи
                main_address VARCHAR(200) NOT NULL,      -- Основной адрес
                additional_address VARCHAR(200) NULL,    -- Дополнительный адрес
                required_workers INT NOT NULL,           -- Количество человек
                worker_price NUMERIC(10, 2) NOT NULL,    -- Цена исполнителю
                assigned_performers BIGINT[] NULL,       -- Список исполнителей
                task_status VARCHAR(30) NOT NULL         -- Статус задачи
                    DEFAULT 'Назначено'           
                    CHECK (task_status IN ('Назначено', 'Работники найдены', 'Завершено', 'Отменено'))
            );
            CREATE TABLE IF NOT EXISTS task_performers (
                task_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                PRIMARY KEY (task_id, user_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id_tasks) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id_users) ON DELETE CASCADE
            );
        """)
        connection.commit()
        print("Таблицы успешно созданы или уже существует.")
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

