from prettytable import PrettyTable


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
    """Создает таблицу для просмотра задач."""
    table = PrettyTable()
    table.field_names = ['#', 'Адрес', 'Описание', 'Статус']

    # Настраиваем выравнивание всех колонок
    table.align['Адрес'] = 'l'
    table.align['Описание'] = 'l'
    table.align['Статус'] = 'l'

    # Устанавливаем максимальную ширину колонок
    table._max_width = {
        'Адрес': 30,
        'Описание': 50,
        'Статус': 20
    }

    # Добавляем строки из результатов запроса
    for task in tasks:
        executor_text = task[8] if task[8] is not None else 'Не назначен'

        # Обрезаем текст целыми словами
        def truncate_text(text, max_length):
            if len(text) <= max_length:
                return text
            # Находим последнее слово перед лимитом
            truncated = text[:max_length].rsplit(None, 1)[0]
            return truncated + '...'

        description = truncate_text(task[6], 47)  # 47 чтобы учесть '...'

        table.add_row([
            task[0],  # id_task
            task[5],  # address
            description,  # task_text
            task[7],  # task_status
        ])

    # Форматируем и обернём в код-блок для сохранения форматирования
    return f"```\n{table.get_string()}\n```"
