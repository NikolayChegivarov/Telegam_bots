from telebot import TeleBot, types
from database import connect_to_database, check_and_create_db, initialize_database
from functions import get_user_ids, availability_organization, availability_first_name, availability_last_name, \
    format_tasks_admin, format_tasks_client
from interaction import access_check, request_organization, client, admin_menu, alter_status, start_command
# Загрузка переменных окружения
import os
from dotenv import load_dotenv

load_dotenv()

# Создание экземпляра бота ТОЛЬКО ЗДЕСЬ!
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


# Добавить обработчики оплаты СЮДА
@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_query_handler(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def successful_payment_handler(message):
    bot.send_message(message.chat.id, "Оплата прошла успешно! Спасибо за покупку.")


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
        return admin_menu(bot)

    # ПРОВЕРКА ДОСТУПА:
    user_ids = get_user_ids(cursor)
    if user_ids:
        print(f"Найдено {len(user_ids)} пользователей: \n{user_ids}")
    else:
        print("Пользователи не найдены в бд.\n")

    # Если нет в бд, отдаем на проверку админу.
    if user_id not in user_ids:
        print(f'Пользователя {user_id} нет в базе данных.')
        bot.send_message(user_id,
                         'У вас нет доступа к чату. Придется немного подождать пока администратор вас не добавит.')
        text = f"Пользователь хочет добавиться в рабочий чат: \n{user_info}"
        bot.send_message(ADMIN, text)
        access_check(bot, user_id)
        return 'ok'
    # Если пользователь есть в бд.
    else:
        print(f"Пользователь {user_id} есть в базе данных.")

        # Проверяем заполнен ли тип клиента.
        organization_result = availability_organization(cursor, user_id)
        if organization_result is None or organization_result[0] is None:
            print('\nНе указана организация!')
            bot.send_message(user_id, 'Введите название организации.')
            return bot.register_next_step_handler_by_chat_id(user_id, organization_we_get)
        else:
            print(f"Организация: {organization_result[0]}")

        # Проверяем наличие имени клиента
        first_name_result = availability_first_name(cursor, user_id)
        if first_name_result is None or first_name_result[0] is None:
            print(f"\nНе указано имя!")
            bot.send_message(user_id, 'Введите имя.')
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
        client(bot, user_id)
    return 'ok'


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    print(f"=== CALLBACK ОБРАБОТКА ===")
    print(f"Пользователь {chat_id} Нажал кнопку {call.data}")
    print(f"Текст сообщения: '{call.message.text}'")
    print("========================")

    # Сразу подтверждаем получение запроса
    bot.answer_callback_query(callback_query_id=call.id)

    if call.data == 'accept':
        try:
            # Ищем ID в тексте сообщения
            import re
            text = call.message.text
            numbers = re.findall(r'\d+', text)
            if numbers:
                user_id = int(numbers[-1])
                print(f"Найдено число в тексте: {user_id}")
            else:
                # Если в тексте только число
                user_id = int(text.strip())

            print(f"согласовал пользователя {user_id}")

            params = (user_id,)
            update_query = """
                INSERT INTO users (id_user_telegram, first_name, last_name, user_status)
                VALUES (%s, NULL, NULL, NULL)
            """
            cursor.execute(update_query, params)
            cnx.commit()
            request_organization(bot, user_id)
            bot.send_message(ADMIN, f"Пользователь {user_id} добавлен в бд.")
            print(f"Пользователь {user_id} добавлен в базу данных.")

        except Exception as e:
            print(f"Ошибка при обработке accept: {e}")
            bot.send_message(ADMIN, f"Ошибка: {e}")

    elif call.data == 'reject':
        try:
            import re
            text = call.message.text
            numbers = re.findall(r'\d+', text)
            if numbers:
                user_id = int(numbers[-1])
            else:
                user_id = int(text.strip())

            print(f"не согласовал пользователя {user_id}")
            bot.send_message(user_id, 'Вам отказано в доступе.')
        except Exception as e:
            print(f"Ошибка при обработке reject: {e}")

    elif call.data == 'natural_person':
        print(f"я физ лицо.")
        params = ('ФИЗ ЛИЦО', chat_id)
        update_query = """
            UPDATE users
            SET organization = %s
            WHERE id_user_telegram = %s
        """
        cursor.execute(update_query, params)
        cnx.commit()
        print(f"Тип клиента {chat_id} установлен.\n")

        bot.send_message(chat_id, 'Введите имя.')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, first_name_we_get)

    elif call.data == 'organization':
        print(f"я из организации.")

        bot.send_message(chat_id, 'Введите название организации.')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, organization_we_get)

    elif call.data == 'set_a_task':
        print("ставит задачу.")
        bot.send_message(chat_id, 'Поставьте задачу:')
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, set_a_task)

    elif call.data == "tasks":
        print("хочет посмотреть задачи.")
        if chat_id == ADMIN:
            tasks_today = """
                SELECT ta.id_task, ta.created_at, us.organization, us.first_name, us.last_name, ta.task_text, ta.task_status
                FROM tasks ta
                INNER JOIN  users us ON us.id_user_telegram = ta.author
                WHERE task_status != 'Сделано';
            """
            cursor.execute(tasks_today)
            cnx.commit()
            results = cursor.fetchall()
            print(f"Результат: {results}")
            if results:
                text = format_tasks_admin(results)
                bot.send_message(chat_id, text=text, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, text='Задачи отсутствуют')
        else:
            tasks_today = """
                SELECT *
                FROM tasks
                WHERE task_status != 'Сделано';
            """
            cursor.execute(tasks_today)
            cnx.commit()
            results = cursor.fetchall()
            print(f"Результат: {results}")
            if results:
                text = format_tasks_client(results)
                bot.send_message(chat_id, text=text, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, text='Задачи отсутствуют')
        return entrance(call)

    elif call.data == "status":
        print("указывает номер задачи для смены статуса.")
        bot.send_message(chat_id, "Укажите номер задачи которую хотите изменить.")
        return bot.register_next_step_handler_by_chat_id(chat_id, get_status)

    elif call.data == "work_task" or call.data == "to_mark":
        if call.data == "work_task":
            status = 'В работе'
        elif call.data == "to_mark":
            status = 'Сделано'
        id_task = int(call.message.text.split('№')[-1])
        print(f"меняет статус задачи {id_task} на '{status}'.")

        params = (status, id_task)
        update_query = """
            UPDATE tasks
            SET task_status = %s
            WHERE id_task = %s
        """
        cursor.execute(update_query, params)
        cnx.commit()
        print(f"Статус задачи №{id_task} изменен на '{status}'.\n")

        bot.send_message(chat_id, f"Статус задачи №{id_task} - '{status}'")

        query = """
            SELECT author
            FROM tasks
            WHERE id_task = %s;
        """
        cursor.execute(query, (id_task,))
        result = cursor.fetchone()
        if result:
            author = result[0]
            print(f"author: {author}")
            bot.send_message(author, f"Статус задачи №{id_task} - '{status}'")
        else:
            print("Запись не найдена")

        cnx.commit()
        return admin_menu(bot)

    elif call.data == 'del_task':
        print("хочет удалить задачу.")
        bot.send_message(chat_id, "Укажите номер задачи которую хотите удалить.")
        return bot.register_next_step_handler_by_chat_id(chat_id, del_task)

    elif call.data == "to_payment":
        start_command(bot, chat_id)

    return admin_menu(bot)


# <<<<<<<<<<<< ОБРАБОТЧИКИ "СЛЕДУЮЩЕГО ШАГА" >>>>>>>>>>>>>>>


# ЗНАКОМИМСЯ С ПОЛЬЗОВАТЕЛЕМ.
def organization_we_get(message):
    user_id = message.from_user.id
    organization = message.text
    print(f"Я из организации: {organization}")

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


def first_name_we_get(message):
    user_id = message.from_user.id
    first_name = message.text
    print(f"Меня зовут: {first_name}")

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


def last_name_we_get(message):
    user_id = message.from_user.id
    last_name = message.text
    print(f"Моя фамилия: {last_name}")

    params = (last_name, user_id)
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
    user_id = message.from_user.id
    phone = message.text
    print(f"Мой телефон: {phone}")

    params = (phone, user_id)
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

    new_task = """
        INSERT INTO tasks (author, task_text, task_status)
        VALUES (%s, %s, %s)
        RETURNING id_task
    """
    cursor.execute(new_task, params)
    id_task = cursor.fetchone()[0]
    cnx.commit()
    bot.send_message(user_id, f"Задача {id_task} успешно поставлена.")
    bot.send_message(ADMIN, f"Вам поставлена задача {id_task}.")
    client(bot, user_id)


def get_status(message):
    """Получили номер задачи для смены статуса."""
    print("\nполучили id_task для изменения статуса.")
    id_task = message.text
    user_id = message.from_user.id
    alter_status(bot, user_id, id_task)


def del_task(message):
    print("\nполучили id_task для удаления")
    id_task = message.text
    user_id = message.from_user.id

    delite_task = """
        DELETE
        FROM tasks
        WHERE id_task = %s;
    """
    cursor.execute(delite_task, (id_task,))
    cnx.commit()
    bot.send_message(user_id, f"Задача {id_task} успешно удалена.")
    admin_menu(bot)


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)