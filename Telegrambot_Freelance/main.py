from telebot import TeleBot
import os
from dotenv import load_dotenv
from database import connect_to_database, check_and_create_db, initialize_database
from functions import get_user_ids, availability_organization, availability_first_name, availability_last_name, \
    format_tasks
from interaction import access_check, request_organization, client, admin_menu, alter_status

# Загрузка переменных окружения
load_dotenv()

# Создание экземпляра бота
bot = TeleBot(os.getenv("TELEGRAM_TOKEN_BOT"))

# Проверка и создание базы данных, если она отсутствует
check_and_create_db()

# Инициализация базы данных (создание таблиц, если они отсутствуют)
initialize_database()

# Установление соединения с базой данных
cnx = connect_to_database()
if cnx:
    cursor = cnx.cursor()
    print("Подключение с бд успешно установлено.")
else:
    raise Exception("Не удалось установить соединение с базой данных")

ADMIN = int(os.getenv("ADMIN"))


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

    if user_id == ADMIN:
        return admin_menu()


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
        bot.send_message(ADMIN, text)
        # Сообщение админу с клавиатурой.
        access_check(user_id)
        return 'ok'
    # Если пользователь есть в бд.
    else:
        print(f"Пользователь {user_id} есть в базе данных.")

        # Проверяем заполнен ли тип клиента.
        organization_result = availability_organization(cursor, user_id)
        if organization_result is None or organization_result[0] is None:
            print('\nНе указана организация!')
            # Отправить сообщение с просьбой указать организацию.
            bot.send_message(user_id, 'Введите название организации.')
            # Указываем обработчик следующего шага
            return bot.register_next_step_handler_by_chat_id(user_id, organization_we_get)
        else:
            print(f"Организация: {organization_result[0]}")

        # Проверяем наличие имени клиента
        first_name_result = availability_first_name(cursor, user_id)
        if first_name_result is None or first_name_result[0] is None:
            print(f"\nНе указано имя!")
            # Отправить сообщение с просьбой указать имя.
            bot.send_message(user_id, 'Введите имя.')
            # Указываем обработчик следующего шага
            return bot.register_next_step_handler_by_chat_id(user_id, first_name_we_get)
        else:
            print(f"Имя: {first_name_result[0]}")

        # Проверяем наличие фамилии клиента.
        last_name_result = availability_last_name(cursor, user_id)
        if last_name_result is None or last_name_result[0] is None:
            print(f"\nНе указана фамилия!")
            bot.send_message(user_id, 'Введите фамилию.')
            return bot.register_next_step_handler_by_chat_id(user_id, last_name_we_get)
        elif last_name_result[0]:
            print(f"Фамилия: {last_name_result[0]}")
        client(user_id)
    return 'ok'


# %%%%%%%%%%%% ОБРАБОТЧИК КОМАНД. %%%%%%%%%%%%%%%%%%
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # pprint.pprint(f'Поступившая информация: {call}')
    print(f"Нажата кнопка {call.data}")
    chat_id = call.from_user.id
    print(f"Пользователь {chat_id}")

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
        # Пользователю клавиатуру.
        request_organization(user_id)
        # Админу уведомление.
        bot.send_message(ADMIN, f"Пользователь {user_id} добавлен в бд.")
        print(f"Пользователь {user_id} добавлен в базу данных.")
        # Посылаем запрос статуса.
    # Если администратор отказал пользователю.
    elif call.data == 'reject':
        text = call.message.text
        user_id = int(text)
        print(f"не согласовал пользователя {user_id}")
        bot.send_message(user_id, 'Вам отказано в доступе.')

    elif call.data == 'natural_person':
        print(f"я физ лицо.")
        # Параметры.
        params = ('ФИЗ ЛИЦО', chat_id)
        # Указываем тип клиента:
        update_query = """
            UPDATE users
            SET organization = %s
            WHERE id_user_telegram = %s
        """
        # Выполнение запроса с параметрами
        cursor.execute(update_query, params)
        cnx.commit()
        print(f"Тип клиента {chat_id} установлен.\n")

        # Отправить сообщение с просьбой указать имя.
        bot.send_message(chat_id, 'Введите имя.')
        # Указываем обработчик следующего шага
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, first_name_we_get)
    elif call.data == 'organization':
        print(f"я из организации.")

        # Отправить сообщение с просьбой указать организацию.
        bot.send_message(chat_id, 'Введите название организации.')
        # Указываем обработчик следующего шага
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, organization_we_get)
    # Поставить задачу.
    elif call.data == 'set_a_task':
        print("ставит задачу.")
        bot.send_message(chat_id, 'Поставьте задачу:')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, set_a_task)
    elif call.data == "tasks":
        print("хочет посмотреть задачи.")
        tasks_today = """
            SELECT *
            FROM tasks;
        """
        # Выполнение запроса с параметрами
        cursor.execute(tasks_today, )
        cnx.commit()
        results = cursor.fetchall()
        print(f"Результат: {results}")
        if results:
            text = format_tasks(results)
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, text='Задачи отсутствуют')
        return entrance(call)
    elif call.data == "status":
        print("указывает номер задачи для смены статуса.")
        bot.send_message(chat_id,
                         "Укажите номер задачи которую хотите изменить.")
        return bot.register_next_step_handler_by_chat_id(chat_id, get_status)
    elif call.data == "work_task" or call.data == "to_mark":
        if call.data == "work_task":
            status = 'В работе'
        elif call.data == "to_mark":
            status = 'Сделано'
        id_task = int(call.message.text.split('№')[-1])
        print(f"id_task ==== {id_task}")
        # Параметры.
        params = (status, id_task)
        # Указываем тип клиента:
        update_query = """
            UPDATE tasks
            SET task_status = %s
            WHERE id_task = %s
        """
        # Выполнение запроса с параметрами
        cursor.execute(update_query, params)
        cnx.commit()
        print(f"Статус задачи {id_task} изменен на {status}.\n")
        admin_menu()
        pass
    elif call.data == "to_payment":
        pass


# <<<<<<<<<<<< ОБРАБОТЧИКИ "СЛЕДУЮЩЕГО ШАГА" >>>>>>>>>>>>>>>


# ЗНАКОМИМСЯ С ПОЛЬЗОВАТЕЛЕМ.
# Указываем организацию.
def organization_we_get(message):
    user_id = message.from_user.id
    organization = message.text
    print(f"Я из организации: {organization}")

    # Параметры.
    params = (organization, user_id)
    update_query = """
        UPDATE users
        SET organization = %s
        WHERE id_user_telegram = %s
    """
    cursor.execute(update_query, params)
    cnx.commit()

    print(f"Организация {organization} в бд занесена.")

    bot.send_message(message.chat.id, 'Введите Имя.')
    return bot.register_next_step_handler_by_chat_id(message.chat.id, first_name_we_get)


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

    bot.send_message(message.chat.id, "Укажите контактный номер телефона.")
    return bot.register_next_step_handler_by_chat_id(message.chat.id, phone_we_get)


def phone_we_get(message):
    # print(f'СООБЩЕНИЕ {message}')
    user_id = message.from_user.id
    phone = message.text
    print(f"Мой телефон: {phone}")
    # Параметры.
    params = (phone, user_id)

    # Заносим телефон в бд.
    update_query = """
        UPDATE users
        SET phone = %s
        WHERE id_user_telegram = %s
    """
    cursor.execute(update_query, params)
    cnx.commit()
    print(f"Номер телефона {phone} в бд занесен.")

    return entrance(message)


def set_a_task(message):
    print("Получаем задачу, добавляем её в бд.")
    user_id = message.from_user.id
    task = message.text
    status = 'Поставлена'
    params = (user_id, task, status,)
    # Ставим задачу и возвращаем id_task
    new_task = """
        INSERT INTO tasks (author, task_text,  task_status)
        VALUES (%s, %s, %s)
        RETURNING id_task
    """
    # Выполнение запроса с параметрами и получение id_task
    cursor.execute(new_task, params)
    id_task = cursor.fetchone()[0]  # Получаем id_task из результата запроса
    cnx.commit()
    bot.send_message(user_id, f"Задача {id_task} успешно поставлена.")

    client(user_id)


def get_status(message):
    """Получили номер задачи для смены статуса."""
    print("сработал get_status \nполучили id_task")
    id_task = message.text
    user_id = message.from_user.id
    # Сохраняем id_task в словарь состояний
    alter_status(user_id, id_task)


    # Сохраняем id_task в словарь состояний
    # params = (executor, status, id_task,)
    # take_task = """
    #         UPDATE tasks
    #         SET executor = %s,
    #             task_status = %s
    #         WHERE id_task = %s
    #     """
    # cursor.execute(take_task, params)
    # cnx.commit()
    # print("Исполнитель установлен, статус задачи изменен.")


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
