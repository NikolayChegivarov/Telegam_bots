def check_database_connection(bd):
    """Функция проверяет подключение к базе данных"""
    if bd.is_connected():
        print("Подключение к базе данных установлено.")
    else:
        print("Не удалось подключиться к базе данных.")
