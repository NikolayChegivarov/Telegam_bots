from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
import os

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

    tables_to_check = [
        ("users", """
            id_user_telegram BIGINT PRIMARY KEY,
            organization VARCHAR(30) NULL,
            first_name VARCHAR(30) NULL,
            last_name VARCHAR(30) NULL,
            phone VARCHAR(20) NULL,
            user_status VARCHAR(30) NULL,
            my_comment VARCHAR(100) NULL
        """),
        ("tasks", """
            id_task SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            author BIGINT NOT NULL,
            task_text TEXT NOT NULL,
            task_status VARCHAR(30) NOT NULL,
            CONSTRAINT fk_tasks_author
            FOREIGN KEY (author)
            REFERENCES users(id_user_telegram) ON DELETE CASCADE
        """)
    ]

    try:
        connection.autocommit = True
        cursor = connection.cursor()

        for table_name, table_schema in tables_to_check:
            # Проверка наличия таблицы
            cursor.execute(sql.SQL("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = "
                                   "'public' AND tablename = %s)"), [table_name])
            exists = cursor.fetchone()[0]

            if not exists:
                # Создание таблицы, если она отсутствует
                cursor.execute(sql.SQL("CREATE TABLE {} ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(table_schema)
                ))
                print(f"Таблица {table_name} успешно создана.")
            else:
                print(f"Таблица {table_name} уже существует.")

        cursor.close()
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    check_and_create_db()
    initialize_database()
