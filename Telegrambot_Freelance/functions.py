from datetime import datetime


def get_user_ids(cursor):
    """Функция для получения id всех пользователей."""
    try:
        # Выполняем запрос на получение всех id пользователей
        cursor.execute("SELECT id_user_telegram FROM users")
        # Получаем все результаты
        results = cursor.fetchall()
        # Преобразуем результаты в список id
        id_user_telegram = [row[0] for row in results]
        return id_user_telegram
    except Exception as e:
        # Обработка любых возникших ошибок
        print(f"Произошла ошибка при получении ID пользователей: {str(e)}")
        return []


def availability_organization(cursor, user_id):
    """Запрос типа клиента."""
    params = (user_id,)
    request = """SELECT organization
    FROM users
    WHERE id_user_telegram = %s"""
    cursor.execute(request, params)
    organization_result = cursor.fetchone()
    return organization_result


def availability_first_name(cursor, user_id):
    """Запрос Имени клиента."""
    params = (user_id,)
    request = """SELECT first_name
    FROM users
    WHERE id_user_telegram = %s"""
    cursor.execute(request, params)
    first_name_result = cursor.fetchone()
    return first_name_result


def availability_last_name(cursor, user_id):
    """Запрос Фамилии клиента."""
    params = (user_id,)
    request = """SELECT last_name
    FROM users
    WHERE id_user_telegram = %s"""
    cursor.execute(request, params)
    last_name_result = cursor.fetchone()
    return last_name_result


def format_tasks(tasks):
    """Форматирует задачи в виде текста с переносами строк."""
    result = ""
    for task in tasks:
        created_at = task[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task[1], datetime) else task[1]
        result += f"Задача #{task[0]}\n"
        result += f"Дата: {created_at}\n"
        result += f"Описание: {task[3]}\n"
        result += f"Статус: {task[4]}\n\n"
    return result
