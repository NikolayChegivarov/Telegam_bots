import psycopg2
from dotenv import load_dotenv
import os

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.required_vars = ['HOST', 'DB_USER', 'DB_PASSWORD', 'DB_PORT', 'DB_NAME']

        self.db_params = {
            'host': os.getenv('HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT'),
            'dbname': os.getenv('DB_NAME')
        }
        self._validate_db_params()

    def _validate_db_params(self):
        missing_params = [key for key, value in self.db_params.items() if not value]
        if missing_params:
            raise ValueError(f"Отсутствуют обязательные параметры подключения: {', '.join(missing_params)}")

    def check_env_variables(self):
        try:
            self._validate_db_params()
            return "Все переменные окружения доступны"
        except ValueError as e:
            return str(e)

    def _get_connection(self, database=None):
        params = self.db_params.copy()
        if database == 'postgres':
            params['dbname'] = 'postgres'
        elif database:
            params['dbname'] = database
        return psycopg2.connect(**params)

    def check_postgres_connection(self):
        try:
            with self._get_connection('postgres') as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return "Подключение к postgres успешно установлено"
        except psycopg2.OperationalError as e:
            return f"Ошибка подключения: {e}"
        except Exception as e:
            return f"Непредвиденная ошибка: {e}"

    def check_and_create_db(self):
        db_name = self.db_params['dbname']
        if not db_name:
            return "Ошибка: имя базы данных не указано"
        try:
            conn = self._get_connection('postgres')
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 FROM pg_database 
                    WHERE datname = %s
                """, (db_name.lower(),))
                exists = cursor.fetchone()
                if not exists:
                    cursor.execute(f'CREATE DATABASE "{db_name}"')
                    return f"База данных {db_name} успешно создана"
                return f"База данных {db_name} уже существует"
        except psycopg2.Error as e:
            return f"Ошибка PostgreSQL: {e}"
        except Exception as e:
            return f"Непредвиденная ошибка: {e}"
        finally:
            if 'conn' in locals():
                conn.close()

    def create_tables(self):
        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id_user_telegram BIGINT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL
                        DEFAULT 'Заблокированный'
                        CHECK (status IN ('Активный', 'Заблокированный', 'В ожидании')),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'reports_history': """
                CREATE TABLE IF NOT EXISTS reports_history (
                    id SERIAL PRIMARY KEY,
                    org_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
        }

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    results = {}
                    for table_name, query in tables.items():
                        try:
                            cursor.execute(query)
                            results[table_name] = "Создана или уже существует"
                        except psycopg2.Error as e:
                            conn.rollback()
                            results[table_name] = f"{e}"
                    conn.commit()
                    return results
        except psycopg2.Error as e:
            return {"error": f"Ошибка подключения: {e}"}


if __name__ == "__main__":
    db_manager = DatabaseManager()

    print(db_manager.check_env_variables())
    print(db_manager.check_postgres_connection())
    print(db_manager.check_and_create_db())

    result = db_manager.create_tables()
    print("Результат создания таблиц:")
    for table, status in result.items():
        print(f"- {table}: {status}")
