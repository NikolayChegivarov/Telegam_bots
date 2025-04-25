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
                id_users BIGSERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,                              -- Имя
                last_name VARCHAR(50) NOT NULL,                               -- Фамилия
                phone VARCHAR(20) NOT NULL,                                   -- Телефон
                is_loader BOOLEAN NOT NULL DEFAULT FALSE,                     -- Грузчик
                is_driver BOOLEAN NOT NULL DEFAULT FALSE,                     -- Водитель
                is_self_employed BOOLEAN NOT NULL DEFAULT FALSE,              -- Самозанятый
                inn VARCHAR(12) NULL,                                   
                status VARCHAR(20) NOT NULL                                   -- Статус активности
                    DEFAULT 'Активный'
                    CHECK (status IN ('Активный', 'Заблокированный')),
                comment TEXT NULL,                                            -- Комментарий администратора
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP       -- Когда создан
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id_tasks BIGSERIAL PRIMARY KEY, 
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,      -- Дата, время создания задачи
                assignment_date DATE NULL,                                    -- Дата назначения
                assignment_time TIME NULL,                                    -- Время назначения
                task_type VARCHAR(20) NOT NULL                                -- Тип задачи
                    CHECK (task_type IN ('Погрузка', 'Доставка')),            
                description TEXT NOT NULL,                                    -- Описание
                main_address VARCHAR(200) NOT NULL,                           -- Адрес основной
                additional_address VARCHAR(200) NULL,                         -- Адрес дополнительный
                required_workers INT NOT NULL,                                -- Количество работников
                worker_price NUMERIC(10, 2) NOT NULL,                         -- Цена за работу
                assigned_performers BIGINT[] NULL,                            -- Назначенные исполнители
                task_status VARCHAR(30) NOT NULL                              -- Статус задачи
                    DEFAULT 'Назначено'
                    CHECK (task_status IN ('Назначено', 'Работники найдены', 'Завершено', 'Отменено'))
            );
            CREATE TABLE IF NOT EXISTS task_performers (                      -- Связи
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


def create_task(task_data: dict) -> int:
    """
    Создает новую задачу в базе данных
    :param task_data: Словарь с данными задачи (включая worker_price)
    :return: ID созданной задачи
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO tasks (
                assignment_date, 
                assignment_time, 
                task_type, 
                description, 
                main_address, 
                additional_address, 
                required_workers,
                worker_price,
                task_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_tasks
        """

        cursor.execute(query, (
            task_data['date_of_destination'],
            task_data['appointment_time'],
            task_data['type_of_task'],
            task_data['description'],
            task_data['main_address'],
            task_data['additional_address'],
            task_data['required_workers'],
            task_data['worker_price'],  # Используем переданную цену
            'Назначено'
        ))

        task_id = cursor.fetchone()[0]
        connection.commit()
        return task_id
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Ошибка при создании задачи: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()