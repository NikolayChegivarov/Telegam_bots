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


def format_tasks_admin(tasks):
    """Форматирует задачи в виде текста с переносами строк."""
    result = ""
    for task in tasks:
        # Извлекаем данные из кортежа task
        task_id = task[0]
        created_at = task[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task[1], datetime) else task[1]
        organization = task[2] if task[2] else "Не указано"
        first_name = task[3] if task[3] else "Не указано"
        last_name = task[4] if task[4] else "Не указано"
        task_text = task[5]
        task_status = task[6]

        # Формируем строку с информацией о задаче
        result += f"Задача #{task_id}\n"
        result += f"Дата: {created_at}\n"
        result += f"Организация: {organization}\n"
        result += f"Автор: {first_name} {last_name}\n"
        result += f"Описание: {task_text}\n"
        result += f"Статус: {task_status}\n\n"
    return result


def format_tasks_client(tasks):
    """Форматирует задачи в виде текста с переносами строк."""
    result = ""
    for task in tasks:
        created_at = task[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task[1], datetime) else task[1]
        result += f"Задача #{task[0]}\n"
        result += f"Дата: {created_at}\n"
        result += f"Описание: {task[3]}\n"
        result += f"Статус: {task[4]}\n\n"
    return result
