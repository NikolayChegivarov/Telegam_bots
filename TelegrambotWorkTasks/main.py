from functions import get_user_ids, status_request, format_tasks
from utils import create_bot, get_db_connection
from interaction import send_welcome, manager, driver, access_check, create_calendar, view_filter_task, \
    alter_status_views
from database import check_and_create_tables
from datetime import datetime
import ast  # Модуль для безопасного преобразования строки в словарь
from database import execute_sql_query  # функция для выполнения SQL запросов.
import pprint
import re

import os
from sqlalchemy import create_engine

# Настройка уровня логирования
# import logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('sqlalchemy.engine')
# logger.setLevel(logging.INFO)

# Создание движка SQLAlchemy
# engine = create_engine(
#     f'postgresql://{os.environ["USER"]}:{os.environ["PASSWORD_DB"]}@{os.environ["HOST"]}/{os.environ["NAME_DB"]}')

# Подключение к боту.
bot = create_bot()

# Подключение к бд.
try:
    # Получаем соединение с базой данных
    cnx, cursor = get_db_connection()
    # Проверяем и создаем таблицы если необходимо
    check_and_create_tables(cursor)
    cnx.commit()  # Применяем изменения
except ConnectionError as e:
    print(f"Ошибка при подключении к базе данных: {e}")
    # logger.error(f"Ошибка при подключении к базе данных: {e}")
    exit(1)


@bot.message_handler(func=lambda message: True)
def entrance(message):
    print("=== ВХОД / entrance ===")

    user_id = message.from_user.id
    first_name = message.from_user.first_name if message.from_user.first_name else None
    username = message.from_user.username if message.from_user.username else None
    last_name = message.from_user.last_name if message.from_user.last_name else None
    user_info = {"user_id": user_id,
                 "username": username,
                 "first_name": first_name,
                 "last_name": last_name
                 }
    print(f"\nИнформация о пользователе: \n{user_info}\n")

    # ПРОВЕРКА ДОСТУПА:
    # Получаем список id пользователей из бд.
    user_ids = get_user_ids(cursor)
    # Работаем с результатами
    if user_ids:
        print(f"Найдено {len(user_ids)} пользователей: \n{user_ids}")
    else:
        print("Пользователи не найдены в бд.\n")

    # Если нет в бд, отдаем на проверку админу.
    if user_id not in user_ids:
        print(f'Пользователя {user_id} нет в базе данных.')
        # Сообщение пользователю.
        bot.send_message(user_id,
                         'У вас нет доступа к чату. Придется немного подождать пока администратор вас не добавит.')
        # Сообщение админу с информацией.
        text = f"Пользователь хочет добавиться в рабочий чат: \n{user_info}"
        bot.send_message(476822305, text)
        # Сообщение админу с клавиатурой.
        access_check(user_id)
        return 'ok'
    # Если пользователь есть в бд.
    else:
        print(f"Пользователь {user_id} есть в базе данных.")
        # Проверяем статус.
        status_result = status_request(cursor, user_id)

        if status_result is None:
            print('\nНет статуса. Кто ты воин?')
            # Отправляем сообщение на уточнение статуса:
            send_welcome(user_id)
        elif status_result[0] == "Водитель":
            print(f"\nДа это же водитель!")
            # Высылаем начальную клавиатуру для водителя.
            driver(user_id)
        elif status_result[0] == "Менеджер":
            print(f"\nДа это же менеджер!")
            # Высылаем начальную клавиатуру для водителя.
            manager(user_id)
        else:
            print(f'сработало else')
    return 'ok'


# ОБРАБОТЧИК КОМАНД.
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # pprint.pprint(f'Поступившая информация: {call}')
    print(f"Нажата кнопка {call.data}")
    chat_id = call.from_user.id
    print(f"\nПользователь {chat_id}")

    # Сразу подтверждаем получение запроса
    bot.answer_callback_query(callback_query_id=call.id)

    if call.data == 'accept':
        text = call.message.text
        user_id = int(text)
        print(f"согласовал пользователя {user_id}")

        params = (user_id, )
        update_query = """
            INSERT INTO users (id_user_telegram, first_name, last_name, user_status)
            VALUES (%s, NULL, NULL, NULL)
        """
        cursor.execute(update_query, params)
        cnx.commit()
        # Пользователю клавиатуру, админу уведомление.
        send_welcome(user_id)
        bot.send_message(476822305, f"Пользователь {user_id} добавлен в бд.")
        print(f"Пользователь {user_id} добавлен в базу данных.")
        # Посылаем запрос статуса.
    # Если администратор отказал пользователю.
    elif call.data == 'reject':
        text = call.message.text
        user_id = int(text)
        print(f"не согласовал пользователя {user_id}")
        bot.send_message(user_id, 'Вам отказано в доступе.')
    # Если водитель:
    elif call.data == 'knight':
        print(f"Я рыцарь дорог!")
        # Параметры.
        params = ('Водитель', chat_id)
        # Указываем статус:
        update_query = """
            UPDATE users
            SET user_status = %s
            WHERE id_user_telegram = %s
        """
        # Выполнение запроса с параметрами
        cursor.execute(update_query, params)
        cnx.commit()
        print(f"Статус {chat_id} обновлен на 'Водитель'.\n")

        # Отправить сообщение с просьбой указать имя и зарегистрировать обработчика следующего шага
        bot.send_message(chat_id, 'Введите имя.')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, first_name_we_get)
    # Если менеджер:
    elif call.data == 'mouse':
        print(f"Я мышь офисная!")
        params = ('Менеджер', chat_id)
        # Указываем статус:
        update_query = """
            UPDATE users
            SET user_status = %s
            WHERE id_user_telegram = %s
        """
        # Выполнение запроса с параметрами
        cursor.execute(update_query, params)
        cnx.commit()
        print(f"Статус {chat_id} обновлен на 'Менеджер'.\n")
        # Отправить сообщение с просьбой указать имя и зарегистрировать обработчика следующего шага
        bot.send_message(chat_id, 'Введите имя.')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, first_name_we_get)
    # Поставить задачу.
    elif call.data == 'set_a_task':
        print("ставит задачу.")
        bot.send_message(chat_id, 'Поставьте задачу:')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, set_a_task)
    elif call.data == "tasks":
        print("хочет посмотреть задачи.")
        # Отправляем клавиатуру - выбор задач.
        view_filter_task(chat_id)
    elif call.data == "basic_menu":
        print("возвращается в основное меню.")
        # Отправляем клавиатуру - основное меню.
        return entrance(call)
    elif call.data == "kostroma":
        print("просматривает задачи на сегодня.")
        date = datetime.today().strftime('%d.%m.%Y')
        params = (date, )
        # Задачи на сегодня:
        tasks_today = """
            SELECT *
            FROM tasks
            WHERE date = %s AND city = 'Кострома';
        """
        # Выполнение запроса с параметрами
        cursor.execute(tasks_today, params)
        cnx.commit()
        results = cursor.fetchall()
        if results:
            text = format_tasks(results)
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, text='Задачи отсутствуют')
        return entrance(call)
    elif call.data == "msk":
        print("просматривает задачи на сегодня.")
        date = datetime.today().strftime('%d.%m.%Y')
        params = (date, )
        # Задачи на сегодня:
        tasks_today = """
            SELECT *
            FROM tasks
            WHERE date = %s AND city = 'Москва';
        """
        # Выполнение запроса с параметрами
        cursor.execute(tasks_today, params)
        cnx.commit()
        results = cursor.fetchall()
        if results:
            text = format_tasks(results)
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, text='Задачи отсутствуют')
        return entrance(call)
    elif call.data == "filter":
        print("фильтрует задачу.")
        # Спрашиваем город и дату
        bot.send_message(chat_id, 'В каком городе вы хотите посмотреть задачи:')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, filter_city)
    # Обработка навигации по месяцам
    elif call.data.startswith('prev-month:') or call.data.startswith('next-month:'):
        print("меняет месяц")
        bot.answer_callback_query(call.id)
        year, month = map(int, call.data.split(':')[1:])

        if call.data.startswith('prev-month:'):
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        else:
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_calendar
        )
    # Обработка календаря
    elif call.data.startswith('day:'):
        print("получает дату,")
        data = call.data
        print(f"data = {data}")
        parts = data.split(':')
        # Извлекаем год, месяц и день
        year = int(parts[1])
        month = int(parts[2])
        day = int(parts[3])
        selected_date = datetime(year, month, day)
        # Извлекаем словарь (последний элемент после split)
        dict_str = ':'.join(parts[4:])  # Объединяем оставшиеся части, чтобы получить строку словаря
        argument = ast.literal_eval(dict_str)  # Преобразуем строку в словарь
        if 'id_task' in argument:
            print("записывает дату задачи.")
            bot.answer_callback_query(call.id)
            id_task = argument['id_task']
            params = (selected_date, id_task,)
            update_date = """
                UPDATE tasks 
                SET date = %s
                WHERE id_task = %s
            """
            cursor.execute(update_date, params)
            cnx.commit()
            bot.send_message(chat_id,
                             f"Задача поставлена на {selected_date.strftime('%d.%m.%Y')}")

            # Рассылаем исполнителям уведомление о задаче.
            ids_performers = performers()
            print(f"ids_performers : {ids_performers}")
            for id_performer in ids_performers:
                bot.send_message(id_performer,
                                 f"Задача поставлена {id_task}")

            return entrance(call)
        if 'city' in argument:
            print("выводит задачи на указанную дату, город.")
            city = argument['city']
            params = (selected_date, city, )
            # Задачи:
            tasks_today = """
                SELECT *
                FROM tasks
                WHERE date = %s AND city = %s;
            """
            # Выполнение запроса с параметрами
            cursor.execute(tasks_today, params)
            cnx.commit()
            results = cursor.fetchall()
            if results:
                text = format_tasks(results)
                bot.send_message(chat_id, text, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, text='Задачи отсутствуют')
            return entrance(call)
    elif call.data == "status":
        print("указывает номер задачи для смены статуса.")
        bot.send_message(chat_id,
                         "Укажите номер задачи которую хотите изменить.")
        return bot.register_next_step_handler_by_chat_id(chat_id, get_status)
    elif call.data == "take_task":
        print("указывает исполнителя, меняем статус задачи.")
        executor = chat_id
        status = "В РАБОТЕ"
        text = call.message.text
        match = re.search(r'№(\d+)', text)
        id_task = int(match.group(1))
        print(f"id_task ===== {id_task}")
        params = (executor, status, id_task,)
        take_task = """
                UPDATE tasks
                SET executor = %s,
                    task_status = %s
                WHERE id_task = %s
            """
        cursor.execute(take_task, params)
        cnx.commit()
        print("Исполнитель установлен, статус задачи изменен.")
        return entrance(call)
    elif call.data == "to_mark":
        print("указывает исполнителя, меняем статус задачи.")
        executor = chat_id
        status = "ГОТОВО"
        text = call.message.text
        match = re.search(r'№(\d+)', text)
        id_task = int(match.group(1))
        print(f"id_task ===== {id_task}")
        params = (executor, status, id_task,)
        take_task = """
                UPDATE tasks
                SET executor = %s,
                    task_status = %s
                WHERE id_task = %s
            """
        cursor.execute(take_task, params)
        cnx.commit()
        print("Исполнитель установлен, статус задачи изменен.")
        return entrance(call)
    elif call.data == "my_tasks":
        params = (chat_id, )
        my_task = """
                SELECT *
                FROM tasks
                WHERE executor = %s
            """
        cursor.execute(my_task, params)
        cnx.commit()
        results = cursor.fetchall()
        if results:
            text = format_tasks(results)
            bot.send_message(chat_id, text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, text='Задачи отсутствуют')
        return entrance(call)
    else:
        print('Сработал блок else callback_query: ')


# ЗНАКОМИМСЯ С ПОЛЬЗОВАТЕЛЕМ.
# Заносим имя в бд.
def first_name_we_get(message):
    user_id = message.from_user.id
    first_name = message.text
    print(f"Меня зовут: {first_name}")

    # Параметры.
    params = (first_name, user_id)
    update_query = """
        UPDATE users
        SET first_name = %s
        WHERE id_user_telegram = %s
    """
    cursor.execute(update_query, params)
    cnx.commit()

    print(f"Имя {first_name} в бд занесено.")

    bot.send_message(message.chat.id, 'Введите фамилию.')
    return bot.register_next_step_handler_by_chat_id(message.chat.id, last_name_we_get)


# Заносим фамилию.
def last_name_we_get(message):
    # print(f'СООБЩЕНИЕ {message}')
    user_id = message.from_user.id
    last_name = message.text
    print(f"Моя фамилия: {last_name}")
    # Параметры.
    params = (last_name, user_id)

    # Заносим имя в бд.
    update_query = """
        UPDATE users
        SET last_name = %s
        WHERE id_user_telegram = %s
    """
    cursor.execute(update_query, params)
    cnx.commit()
    print(f"Фамилия {last_name} в бд занесена.")

    return entrance(message)


# СТАВИМ ЗАДАЧУ:
def set_a_task(message):
    print("Получаем задачу, добавляем её в бд, запрашиваем город.")
    user_id = message.from_user.id
    task = message.text
    status = 'Поставлена'
    params = (user_id, task, status,)
    # Ставим задачу и возвращаем id_task
    new_task = """
        INSERT INTO tasks (date, author, city, address, task_text, task_status, executor)
        VALUES (NULL, %s, NULL, NULL, %s, %s, NULL)
        RETURNING id_task
    """
    # Выполнение запроса с параметрами и получение id_task
    cursor.execute(new_task, params)
    id_task = cursor.fetchone()[0]  # Получаем id_task из результата запроса
    cnx.commit()
    bot.send_message(user_id, "Укажите город: ")
    # Передаем id_task в следующую функцию
    return bot.register_next_step_handler_by_chat_id(user_id, city_task, id_task)


def city_task(message, id_task):
    print("Получили город задачи, сохраняем его, запрашиваем адрес.")
    user_id = message.from_user.id
    city = message.text
    params = (city, id_task,)
    update_sity = """
        UPDATE tasks             
        SET city = %s
        WHERE id_task = %s
    """
    cursor.execute(update_sity, params)
    cnx.commit()
    bot.send_message(user_id, "Укажите адрес: ")
    return bot.register_next_step_handler_by_chat_id(user_id, address_task, id_task)


def address_task(message, id_task):
    print("Получили адрес задачи, сохраняем её, запрашиваем дату.")
    user_id = message.from_user.id
    address = message.text
    params = (address, id_task,)
    update_address = """
        UPDATE tasks 
        SET address = %s
        WHERE id_task = %s
    """
    cursor.execute(update_address, params)
    cnx.commit()

    argument = {"id_task": id_task}
    task_number = argument["id_task"]
    text = f"Укажите на какую дату ставите задачу #{task_number}:"
    bot.send_message(user_id, text,
                     reply_markup=create_calendar(argument))


# ФИЛЬТРУЕМ ЗАДАЧИ
def filter_city(message):
    print("Получили город, запрашиваем дату.")
    user_id = message.from_user.id
    city = message.text

    argument = {"city": city}
    city = argument["city"]
    text = f"Укажите на дату на которую хотите просмотреть задачи по г.{city}:"
    bot.send_message(user_id, text,
                     reply_markup=create_calendar(argument))


def get_status(message):
    """Получили номер задачи для смены статуса."""
    print("сработал get_status")
    id_task = message.text
    user_id = message.from_user.id
    # Сохраняем id_task в словарь состояний
    alter_status_views(user_id, id_task)


# РАССЫЛКА ВОДИТЕЛЯМ.
def performers():
    request = """
    SELECT id_user_telegram 
    FROM users
    WHERE user_status = 'Водитель'
    """
    cursor.execute(request, )
    ids_performers = [row[0] for row in cursor.fetchall()]
    # Возвращаем список ID исполнителей.
    return ids_performers


if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    finally:
        # Закрываем соединение с базой данных после завершения работы бота
        cursor.close()
        cnx.close()
