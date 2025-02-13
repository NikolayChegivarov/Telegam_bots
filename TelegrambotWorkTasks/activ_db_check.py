from psycopg2 import OperationalError


def activ_check(cursor):
    """
    Проверяет активные базы данных и определяет текущую активную базу данных.

    Args:
        cursor (psycopg2 cursor): Указатель курсора для выполнения SQL-запросов.

    Функция выполняет следующие действия:
    1. Получает список всех активных баз данных.
    2. Определяет текущую активную базу данных по сравнению с параметрами подключения.
    3. Выводит список активных баз данных и текущую активную базу.

    При возникновении ошибки OperationalError выводит сообщение об ошибке.
    """
    try:
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = cursor.fetchall()
        active_db = [db[0] for db in databases if db[0] == cursor.connection.get_dsn_parameters().get('dbname')]
        print(f"Активные базы данных: {', '.join(active_db)}")
        print(f"Текущая активная база данных: {active_db[0]}") if active_db else print("Не удалось определить текущую активную базу данных.")
    except OperationalError as e:
        print(f"Ошибка при проверке активных баз данных: {e}")
