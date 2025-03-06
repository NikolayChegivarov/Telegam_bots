import psycopg2
from database_connection import connect_to_database
import psycopg2.sql


def check_and_create_tables(cursor):
    tables_to_check = [
        ("users", """
            id_user_telegram BIGINT PRIMARY KEY,
            first_name VARCHAR(100) NULL,
            last_name VARCHAR(100) NULL,
            user_status VARCHAR(100) NULL
        """),
        ("tasks", """
            id_task SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date DATE NULL,  
            author BIGINT NOT NULL,
            city TEXT NULL,
            address TEXT NULL,
            task_text TEXT NOT NULL,
            task_status VARCHAR(100) NOT NULL,
            executor BIGINT NULL,
            CONSTRAINT fk_tasks_author
            FOREIGN KEY (author)
            REFERENCES users(id_user_telegram) ON DELETE CASCADE,
            CONSTRAINT fk_tasks_executor
            FOREIGN KEY (executor)
            REFERENCES users(id_user_telegram) ON DELETE SET NULL
        """)
    ]

    for table_name, columns in tables_to_check:
        cursor.execute(psycopg2.sql.SQL("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            )
        """), ['public', table_name])
        has_table = cursor.fetchone()[0]

        if not has_table:
            print(f"Таблица {table_name} не найдена. Создание таблицы...")

            sql = psycopg2.sql.SQL("""
                CREATE TABLE IF NOT EXISTS {schema}.{table} ({columns})
            """).format(
                schema=psycopg2.sql.Identifier('public'),
                table=psycopg2.sql.Identifier(table_name),
                columns=psycopg2.sql.SQL(columns.strip())
            )
            cursor.execute(sql)
            print(f"Таблица {table_name} создана.")


def main():
    """Основная функция программы.
    Устанавливает соединение с базой данных,
    проверяет наличие и создает необходимые таблицы,
    выполняет операции с базой данных,
    а затем закрывает соединение."""
    cnx = connect_to_database()
    if cnx:
        cursor = cnx.cursor()

        # Проверяем наличие и создаем таблицы при необходимости
        check_and_create_tables(cursor)

        cnx.commit()
        cursor.close()
        cnx.close()
    else:
        print("Не удалось установить соединение с базой данных.")


# def execute_sql_query(cnx, cursor, query, params=None):
#     """
#     Выполняет SQL-запрос и возвращает результат.
#
#     Аргументы:
#         cnx (connection): Соединение с базой данных
#         cursor (cursor): Курсор для выполнения запросов
#         query (str): Текст SQL-запроса
#         params (tuple или dict, опционально): Параметры для подстановки в запрос
#
#     Возвращаемое значение:
#         list или None: Результат выполнения запроса или None в случае ошибки
#
#     Примечание:
#         Функция автоматически фиксирует изменения (commit) при успешном выполнении запроса
#         и откатывает транзакцию (rollback) в случае возникновения исключения.
#     """
#     try:
#         if params:
#             cursor.execute(query, params)
#         else:
#             cursor.execute(query)
#         cnx.commit()
#         return cursor.fetchall()
#     except Exception as e:
#         cnx.rollback()
#         return None


if __name__ == "__main__":
    main()