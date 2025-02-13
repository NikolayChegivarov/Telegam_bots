def execute_sql_and_fetch_one(cursor, query):
    """Функция для выполнения SQL-запроса и получения одного результата."""
    cursor.execute(query)
    result = cursor.fetchone()
    return result


def update_wait_timeout(cursor):
    """Увеличиваем параметр wait_timeout который контролирует время ожидания до автоматического закрытия неактивных
    соединений с сервером базы данных."""
    try:
        # возвращает текущее значение сессионного времени ожидания для текущей сессии базы данных.
        session_wait_timeout = execute_sql_and_fetch_one(cursor, "SHOW SESSION VARIABLES LIKE 'wait_timeout'")
        # возвращает глобальное значение времени ожидания для всех сессий на сервере базы данных.
        global_wait_timeout = execute_sql_and_fetch_one(cursor, "SHOW GLOBAL VARIABLES LIKE 'wait_timeout'")
        print(f'Session wait timeout: {session_wait_timeout[1]} seconds')
        print(f'Global wait timeout: {global_wait_timeout[1]} seconds')
    except Exception as e:
        print(f"Ошибка при получении настроек времени ожидания: {e}")

    # устанавливает максимальное время ожидания для текущей сессии перед тем,
    # как соединение будет автоматически закрыто из-за не активности.
    cursor.execute("SET SESSION wait_timeout=28800")

    new_session_wait_timeout = execute_sql_and_fetch_one(cursor, "SHOW SESSION VARIABLES LIKE 'wait_timeout'")
    print(f'Тайм-аут ожидания нового сеанса: {new_session_wait_timeout[1]} секунд.')

    # Проверка, что значение действительно изменилось
    if new_session_wait_timeout[1] == '28800':
        print("wait_timeout успешно обновлен.")
    else:
        print("Не удалось обновить wait_timeout.")
