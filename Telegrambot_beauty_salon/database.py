import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()


def connect_to_database(dbname=None):
    """Функция устанавливает подключение к базе данных"""
    dbname = dbname or os.getenv("NAME_DB")
    try:
        print(f"Попытка подключения к базе данных '{dbname}'...")
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=dbname,
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD_DB"),
            port=os.getenv("PORT")
        )
        print(f"Успешное подключение к базе данных '{dbname}'")
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Ошибка при подключении к PostgreSQL (база '{dbname}'): {error}")
        return None


def check_and_create_db():
    """Проверка наличия базы данных и её создание при необходимости"""
    print("\n" + "=" * 50)
    print("Проверка существования базы данных...")
    print("=" * 50)

    conn = connect_to_database(dbname="postgres")
    if not conn:
        print("❌ Не удалось подключиться к серверу PostgreSQL")
        return False

    try:
        conn.autocommit = True
        with conn.cursor() as cursor:
            db_name = os.getenv("NAME_DB")
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [db_name])

            if not cursor.fetchone():
                print(f"База данных '{db_name}' не найдена, создаем...")
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"✅ База данных '{db_name}' успешно создана")
                return True
            else:
                print(f"База данных '{db_name}' уже существует")
                return True
    except Exception as e:
        print(f"❌ Ошибка при проверке/создании БД: {e}")
        return False
    finally:
        conn.close()
        print("Соединение с сервером PostgreSQL закрыто")


def initialize_database():
    """Инициализация базы данных и создание таблиц"""
    print("\n" + "=" * 50)
    print("Инициализация базы данных и таблиц")
    print("=" * 50)

    conn = connect_to_database()
    if not conn:
        print("❌ Не удалось подключиться к целевой базе данных")
        return

    tables = [
        ("status", """
            id_status SERIAL PRIMARY KEY,
            status_user VARCHAR(10) NOT NULL UNIQUE
        """, "INSERT INTO status (status_user) VALUES ('ACTIV'), ('LOCKED'), ('VIP')"),

        ("type", """
            id_user_type SERIAL PRIMARY KEY,
            type_user VARCHAR(10) NOT NULL UNIQUE
        """, "INSERT INTO type (type_user) VALUES ('CLIENT'), ('MASTER'), ('ADMIN')"),

        ("users", """
            id_user_telegram BIGINT PRIMARY KEY,
            first_name VARCHAR(30) NULL,
            last_name VARCHAR(30) NULL,
            phone VARCHAR(20),
            id_status INTEGER NOT NULL DEFAULT 1,
            id_user_type INTEGER NOT NULL DEFAULT 1,
            specialization TEXT,
            photo BYTEA,
            my_comment VARCHAR(100),
            FOREIGN KEY (id_status) REFERENCES status (id_status),
            FOREIGN KEY (id_user_type) REFERENCES type (id_user_type)
        """, None),

        ("services", """
            id_services SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            duration INTEGER NOT NULL
        """, None),

        ("record", """
            id_record SERIAL PRIMARY KEY,
            id_service INTEGER NOT NULL,
            id_client BIGINT NOT NULL,
            id_master BIGINT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            FOREIGN KEY (id_service) REFERENCES services (id_services),
            FOREIGN KEY (id_client) REFERENCES users (id_user_telegram),
            FOREIGN KEY (id_master) REFERENCES users (id_user_telegram)
        """, None)
    ]

    try:
        with conn:
            with conn.cursor() as cursor:
                for table_name, table_schema, initial_data in tables:
                    # Проверяем существование таблицы
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_tables 
                            WHERE schemaname = 'public' AND tablename = %s
                        )
                    """, [table_name])

                    exists = cursor.fetchone()[0]

                    if exists:
                        print(f"Таблица '{table_name}' уже существует")
                        continue

                    # Создаем таблицу
                    print(f"Создание таблицы '{table_name}'...")
                    cursor.execute(sql.SQL("CREATE TABLE {} ({})").format(
                        sql.Identifier(table_name),
                        sql.SQL(table_schema)
                    ))
                    print(f"✅ Таблица '{table_name}' успешно создана")

                    # Добавляем начальные данные, если они указаны
                    if initial_data:
                        print(f"Добавление начальных данных в '{table_name}'...")
                        cursor.execute(initial_data)
                        print(f"✅ Данные добавлены в '{table_name}'")

                    print("\nВсе операции с таблицами завершены успешно")

    except Exception as e:
        print(f"\n❌ Ошибка при инициализации базы данных: {e}")
    finally:
        conn.close()
        print("Соединение с базой данных закрыто")


if __name__ == "__main__":
    print("=" * 50)
    print("Начало работы скрипта инициализации базы данных")
    print("=" * 50)

    if check_and_create_db():
        initialize_database()

    print("\n" + "=" * 50)
    print("Работа скрипта завершена")
    print("=" * 50)
