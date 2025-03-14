from prettytable import PrettyTable
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


def status_request(cursor, user_id):
    """Запрос статуса конкретного пользователя."""
    params = (user_id,)
    request = """SELECT user_status
    FROM users
    WHERE id_user_telegram = %s"""
    cursor.execute(request, params)
    status_result = cursor.fetchone()
    return status_result


def format_tasks(tasks):
    """Форматирует задачи в виде текста с переносами строк."""
    result = ""
    for task in tasks:
        # Извлекаем данные из кортежа task
        task_id = task[0]
        created_at = task[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task[1], datetime) else task[1]
        date = task[2].strftime('%d.%m.%Y') if isinstance(task[2], datetime) else task[2]
        author_firstname = task[3] if task[3] else "Не указано"
        author_lastname = task[4] if task[4] else "Не указано"
        city = task[5]
        address = task[6]
        task_text = task[7]
        status = task[8]

        # Данные об исполнителе (позиции 9 и 10)
        executor_firstname = task[9] if task[9] else "Не указано"
        executor_lastname = task[10] if task[10] else "Не указано"

        # Формируем строку с информацией о задаче
        result += f"Задача #{task_id}\n"
        result += f"Создано: {created_at}\n"
        result += f"Дата: {date}\n"
        result += f"Автор: {author_firstname} {author_lastname}\n"
        result += f"Город: {city}\n"
        result += f"Адрес: {address}\n"
        result += f"Задача: {task_text}\n"
        result += f"Статус: {status}\n"

        # Добавляем информацию об исполнителе с учетом NULL значений
        if executor_firstname != "Не указано" or executor_lastname != "Не указано":
            result += f"Исполнитель: {executor_firstname} {executor_lastname}\n"
        else:
            result += f"Исполнитель: Не назначен\n"

        result += "\n"

    return result