from venv import logger

import psycopg2
from aiogram import Bot
from psycopg2 import sql
from psycopg2.extras import DictCursor
import os


from config import Config

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="Loading_unloading",
        user="postgres",
        password="0000",
        port=Config.DB_PORT
    )


def connect_to_database(dbname="Loading_unloading"):
    """Функция устанавливает подключение к базе данных указанной в аргументе."""
    try:
        connection = psycopg2.connect(
            host="localhost",
            database=dbname,
            user="postgres",
            password="0000",
            port=5432
        )
        connection.autocommit = True  # Добавляем автокоммит
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при подключении к PostgreSQL (база {dbname}): {error}")
        return None


def check_and_create_db():
    """Проверка наличия базы данных и её создание, если она отсутствует."""
    try:
        # Попробуем подключиться напрямую к целевой базе
        test_conn = connect_to_database("Loading_unloading")
        if test_conn:
            test_conn.close()
            print(f"База данных {Config.DB_NAME} уже существует.")
            return True

        # Если не получилось - создаем базу
        admin_conn = connect_to_database("postgres")
        if not admin_conn:
            print("Не удалось подключиться к серверу PostgreSQL")
            return False

        admin_conn.autocommit = True
        with admin_conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(Config.DB_NAME)
                )
            )
        print(f"База данных {Config.DB_NAME} успешно создана.")
        return True

    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
        return False
    finally:
        if 'admin_conn' in locals() and admin_conn:
            admin_conn.close()


def initialize_database():
    """Функция для инициализации базы данных, включая создание всех таблиц, если они отсутствуют."""
    connection = None
    try:
        connection = connect_to_database("Loading_unloading")
        if not connection:
            print("Не удалось подключиться к базе данных Loading_unloading")
            return False

        with connection.cursor() as cursor:
            # Проверяем существование основных таблиц
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'tasks', 'performer_stats', 'task_performers');
            """)
            existing_tables = cursor.fetchone()[0]

            if existing_tables == 4:  # Все 4 таблицы уже существуют
                print("Все таблицы уже существуют.")
                return True

            # Создаем таблицы, если их нет
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id_user_telegram BIGINT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    is_loader BOOLEAN NOT NULL DEFAULT FALSE,
                    is_driver BOOLEAN NOT NULL DEFAULT FALSE,
                    is_self_employed BOOLEAN NOT NULL DEFAULT FALSE,
                    inn VARCHAR(12) NULL,
                    status VARCHAR(20) NOT NULL 
                        DEFAULT 'Заблокированный'
                        CHECK (status IN ('Активный', 'Заблокированный')),
                    comment TEXT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id_tasks BIGSERIAL PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    assignment_date DATE NULL,
                    assignment_time TIME NULL,
                    task_type VARCHAR(20) NOT NULL
                        CHECK (task_type IN ('Погрузка', 'Доставка')),
                    description TEXT NOT NULL,
                    main_address VARCHAR(200) NOT NULL,
                    additional_address VARCHAR(200) NULL,
                    required_workers INT NOT NULL,
                    worker_price NUMERIC(10, 2) NOT NULL,
                    assigned_performers BIGINT[] NULL,
                    task_status VARCHAR(30) NOT NULL
                        DEFAULT 'Назначена'
                        CHECK (task_status IN ('Назначена', 'Работники найдены', 'Завершено', 'Отменено'))
                );

                CREATE TABLE IF NOT EXISTS performer_stats (
                    id_user_telegram BIGINT PRIMARY KEY REFERENCES users(id_user_telegram) ON DELETE CASCADE,
                    total_assigned INT NOT NULL DEFAULT 0,
                    completed INT NOT NULL DEFAULT 0,
                    canceled INT NOT NULL DEFAULT 0,
                    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS task_performers (
                    task_id BIGINT NOT NULL,
                    id_user_telegram BIGINT NOT NULL,
                    PRIMARY KEY (task_id, id_user_telegram),
                    FOREIGN KEY (task_id) REFERENCES tasks(id_tasks) ON DELETE CASCADE,
                    FOREIGN KEY (id_user_telegram) REFERENCES users(id_user_telegram) ON DELETE CASCADE
                );
            """)

            print("Все таблицы успешно созданы или уже существовали.")
            return True

    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        return False
    finally:
        if connection:
            connection.close()


def add_user_to_database(user_id):
    """Добавляет пользователя в базу данных, если его еще нет"""
    try:
        with connect_to_database() as connection:
            if not connection:
                print("Не удалось подключиться к базе данных")
                return False

            with connection.cursor() as cursor:
                # Проверяем существование пользователя
                cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (user_id,))
                exists = cursor.fetchone()

                if not exists:
                    # Добавляем нового пользователя с дефолтными значениями
                    cursor.execute("""
                        INSERT INTO users 
                        (id_user_telegram, first_name, last_name, phone, is_loader, 
                         is_driver, is_self_employed, inn, status, comment)
                        VALUES 
                        (%s, '', '', '', FALSE, FALSE, FALSE, NULL, 'Заблокированный', NULL)
                    """, (user_id,))
                    connection.commit()
                    print(f"Пользователь {user_id} успешно добавлен в базу данных")
                    return True

                print(f"Пользователь {user_id} уже существует в базе данных")
                return False

    except Exception as e:
        print(f"Ошибка при добавлении пользователя {user_id}: {e}")
        return False


def status_verification(user_id):
    """Проверяет, имеет ли пользователь статус 'Активный'"""
    try:
        with connect_to_database() as connection:
            if not connection:
                print("Не удалось подключиться к базе данных")
                return False

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM users WHERE id_user_telegram = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result and result[0] == "Активный"

    except Exception as e:
        print(f"Ошибка при проверке статуса пользователя {user_id}: {e}")
        return False

def checking_your_personal_account(user_id):
    """Проверка на заполненность личного кабинета."""
    connection = connect_to_database()
    if not connection:
        return False

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT first_name, last_name, phone 
                FROM users 
                WHERE id_user_telegram = %s
            """, (user_id,))

            user_data = cursor.fetchone()

            if user_data:
                first_name, last_name, phone = user_data
                if first_name and last_name and phone:
                    return True
            return False
    finally:
        if connection:
            connection.close()


def change_status_user(user_id):
    """Изменяет статус пользователя на 'Активный' (функция администратора)"""
    try:
        with connect_to_database() as connection:
            if not connection:
                print("Не удалось подключиться к базе данных")
                return False

            with connection.cursor() as cursor:
                # Проверяем существование пользователя
                cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (user_id,))
                exists = cursor.fetchone()

                if not exists:
                    print(f"Пользователь {user_id} не найден в базе данных")
                    return False

                # Обновляем статус пользователя
                cursor.execute("""
                    UPDATE users 
                    SET status = 'Активный'
                    WHERE id_user_telegram = %s
                """, (user_id,))

                connection.commit()
                print(f"Статус пользователя {user_id} успешно изменен на 'Активный'")
                return True

    except Exception as e:
        print(f"Ошибка при изменении статуса пользователя {user_id}: {e}")
        return False

def create_task(task_data: dict) -> int:
    """
    Создает новую задачу в базе данных и возвращает её ID
    :param task_data: Словарь с данными задачи {
        'date_of_destination': дата назначения,
        'appointment_time': время назначения,
        'type_of_task': тип задачи,
        'description': описание,
        'main_address': основной адрес,
        'additional_address': дополнительный адрес,
        'required_workers': количество работников,
        'worker_price': цена за работу
    }
    :return: ID созданной задачи
    :raises: Exception в случае ошибки
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                query = """
                    INSERT INTO tasks (
                        assignment_date, 
                        assignment_time, 
                        task_type, 
                        description, 
                        main_address, 
                        additional_address, 
                        required_workers,
                        worker_price,
                        task_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_tasks
                """

                cursor.execute(query, (
                    task_data['date_of_destination'],
                    task_data['appointment_time'],
                    task_data['type_of_task'],
                    task_data['description'],
                    task_data['main_address'],
                    task_data.get('additional_address'),  # Используем get() для опционального поля
                    task_data['required_workers'],
                    task_data['worker_price'],
                    'Назначена'
                ))

                task_id = cursor.fetchone()[0]
                connection.commit()
                return task_id

    except Exception as e:
        print(f"Ошибка при создании задачи: {str(e)}")
        raise  # Пробрасываем исключение дальше для обработки на уровне выше


def get_all_users_type(task_type: str = None) -> list:
    """
    Получает список активных пользователей по указанному типу задачи
    :param task_type: Тип задачи ('Погрузка' или 'Доставка')
    :return: Список ID пользователей (telegram ID)
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT id_user_telegram 
                    FROM users 
                    WHERE status = 'Активный'
                """

                # Добавляем условие в зависимости от типа задачи
                if task_type == 'Погрузка':
                    base_query += " AND is_loader = TRUE"
                elif task_type == 'Доставка':
                    base_query += " AND is_driver = TRUE"
                # Для None или неизвестного типа - возвращаем всех активных пользователей

                cursor.execute(base_query)
                return [row[0] for row in cursor.fetchall()]

    except Exception as e:
        print(f"Ошибка при получении пользователей для типа '{task_type}': {e}")
        return []


def get_pending_tasks(user_type: str = None) -> list[dict]:
    """
    Получает все задачи со статусом 'Назначена' из базы данных
    с фильтрацией по типу задачи, если указан тип пользователя

    Параметры:
        user_type: str - тип пользователя ('loader' или 'driver')

    Возвращает:
        list[dict]: список словарей с информацией о задачах
    """
    try:
        with get_connection() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                base_query = """
                    SELECT 
                        id_tasks,
                        assignment_date as date,
                        assignment_time as time,
                        task_type,
                        description,
                        main_address,
                        additional_address,
                        required_workers,
                        worker_price,
                        assigned_performers
                    FROM tasks
                    WHERE task_status = 'Назначена'
                """

                if user_type == "loader":
                    base_query += " AND task_type = 'Погрузка'"
                elif user_type == "driver":
                    base_query += " AND task_type = 'Доставка'"

                base_query += " ORDER BY assignment_date, assignment_time"

                cursor.execute(base_query)

                return [
                    {
                        'id_tasks': row['id_tasks'],
                        'date': row['date'],
                        'time': row['time'],
                        'task_type': row['task_type'],
                        'description': row['description'],
                        'main_address': row['main_address'],
                        'additional_address': row['additional_address'],
                        'required_workers': row['required_workers'],
                        'worker_price': float(row['worker_price']),
                        'assigned_performers': row['assigned_performers'] or [],
                    }
                    for row in cursor.fetchall()
                ]

    except Exception as e:
        print(f"Ошибка при получении задач для типа '{user_type}': {e}")
        return []


def add_to_assigned_performers(user_id, id_tasks):
    """Добавляет id_user_telegram работника в список assigned_performers определённой задачи
    и обновляет статистику исполнителя"""
    if not isinstance(id_tasks, int):
        return "Некорректный номер задачи"
    try:
        with get_connection() as conn:  # Автоматическое управление соединением
            with conn.cursor() as cursor:
                # Проверяем существование задачи
                cursor.execute("SELECT id_tasks FROM tasks WHERE id_tasks = %s", (id_tasks,))
                if not cursor.fetchone():
                    return "Задача не найдена"

                # Получаем данные задачи
                cursor.execute("""
                    SELECT task_status, required_workers, assigned_performers, 
                           assignment_date, assignment_time, main_address 
                    FROM tasks 
                    WHERE id_tasks = %s
                """, (id_tasks,))
                task_data = cursor.fetchone()

                task_status = task_data[0]

                # Проверяем статус задачи
                if task_status == 'Завершено':
                    return "Задача уже завершена"
                elif task_status == 'Отменено':
                    return "Задача отменена"
                elif task_status == 'Работники найдены':
                    return "Исполнители для задачи уже найдены"
                elif task_status != 'Назначена':
                    return "Невозможно взять задачу: неожиданный статус"

                # Обрабатываем случай, когда статус 'Назначена'
                required_workers = task_data[1]
                assigned_performers = task_data[2] if task_data[2] else []
                remaining_slots = required_workers - len(assigned_performers)

                if remaining_slots <= 0:
                    return f"Исполнители на задачу {id_tasks} уже найдены"

                # Добавляем пользователя в список исполнителей
                assigned_performers.append(user_id)
                cursor.execute("""
                    UPDATE tasks 
                    SET assigned_performers = %s 
                    WHERE id_tasks = %s
                """, (assigned_performers, id_tasks))

                # Добавляем запись в таблицу связей
                cursor.execute("""
                    INSERT INTO task_performers (task_id, id_user_telegram)
                    VALUES (%s, %s)
                """, (id_tasks, user_id))

                # Обновляем статистику исполнителя (увеличиваем счетчик назначенных задач)
                cursor.execute("""
                    INSERT INTO performer_stats (id_user_telegram, total_assigned)
                    VALUES (%s, 1)
                    ON CONFLICT (id_user_telegram) 
                    DO UPDATE SET 
                        total_assigned = performer_stats.total_assigned + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (user_id,))

                # Проверяем, заполнены ли все места
                if remaining_slots == 1:
                    cursor.execute("""
                        UPDATE tasks 
                        SET task_status = 'Работники найдены' 
                        WHERE id_tasks = %s
                    """, (id_tasks,))

                # Фиксируем изменения (не нужно, так как with автоматически коммитит при успехе)

                return (f"Вы взяли задачу {id_tasks}. Просьба прибыть без опозданий "
                        f"{task_data[3]} к {task_data[4]} по адресу {task_data[5]}")

    except Exception as e:
        # В случае ошибки with автоматически откатывает изменения
        return f"Произошла ошибка: {str(e)}"


def get_user_tasks(user_id):
    """
    Возвращает список задач, в которых участвует пользователь со статусом 'Назначена' или 'Работники найдены'

    :param user_id: id пользователя в Telegram
    :return: строка с информацией о задачах или сообщение об их отсутствии
    """
    try:
        with get_connection() as conn:  # Автоматическое управление соединением
            with conn.cursor(cursor_factory=DictCursor) as cursor:  # Используем DictCursor для получения словарей
                # Получаем все активные задачи, где пользователь является исполнителем
                cursor.execute("""
                    SELECT t.* 
                    FROM tasks t
                    JOIN task_performers tp ON t.id_tasks = tp.task_id
                    WHERE tp.id_user_telegram = %s
                    AND t.task_status IN ('Назначена', 'Работники найдены')
                    ORDER BY t.assignment_date, t.assignment_time
                """, (user_id,))

                tasks = cursor.fetchall()

                if not tasks:
                    return "Открытых заявок с вашим участием нет"

                result = []
                for task in tasks:
                    task_info = (
                        f"🆔 Номер задачи: {task['id_tasks']}\n"
                        f"🔹 Тип: {task['task_type']}\n"
                        f"📅 Дата: {task['assignment_date']}\n"
                        f"⏰ Время: {task['assignment_time']}\n"
                        f"📍 Адрес: {task['main_address']}"
                    )

                    if task['additional_address']:
                        task_info += f" ({task['additional_address']})"

                    task_info += (
                        f"\n📝 Описание: {task['description']}\n"
                        f"👷 Требуется работников: {task['required_workers']}\n"
                        f"💰 Цена за работу: {task['worker_price']} руб.\n"
                        f"────────────────────"
                    )

                    result.append(task_info)

                return "\n\n".join(result)

    except Exception as e:
        print(f"Ошибка при получении задач пользователя: {e}")
        return "Произошла ошибка при получении данных о задачах"


def my_data(user_id):
    """Получить данные пользователя по его ID в Telegram"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        first_name, 
                        last_name, 
                        phone, 
                        is_loader, 
                        is_driver, 
                        is_self_employed
                    FROM users
                    WHERE id_user_telegram = %s
                """, (user_id,))

                user_data = cursor.fetchone()

                if user_data:
                    # Формируем строку с эмодзи
                    result = (
                        f"👤 Профиль пользователя:\n\n"
                        f"👨‍💼 Имя: {user_data['first_name']} {user_data['last_name']}\n"
                        f"📱 Телефон: {user_data['phone']}\n"
                        f"🔧 Роли:\n"
                        f"{'✅' if user_data['is_loader'] else '❌'} Грузчик\n"
                        f"{'✅' if user_data['is_driver'] else '❌'} Водитель\n"
                        f"{'✅' if user_data['is_self_employed'] else '❌'} Самозанятый"
                    )
                    return result
                else:
                    return "❌ Пользователь не найден"

    except Exception as e:
        print(f"Ошибка при получении данных пользователя: {e}")
        return "⚠️ Произошла ошибка при получении данных"


def contractor_statistics(user_id: int) -> str:
    """Возвращает статистику исполнителя в формате:
    📊 Статистика заказов:
    • Взял X
    • Выполнил Y (Z%)
    • Отказался W (V%)
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Получаем статистику исполнителя
                cursor.execute("""
                    SELECT total_assigned, completed, canceled
                    FROM performer_stats
                    WHERE id_user_telegram = %s
                """, (user_id,))

                stats = cursor.fetchone()

                if not stats:
                    # Если записи нет, значит исполнитель ещё не брал задач
                    return """📊 Статистика заказов:
                        • Взял 0
                        • Выполнил 0 (0%)
                        • Отказался 0 (0%)"""

                total_assigned, completed, canceled = stats

                # Рассчитываем проценты (избегаем деления на ноль)
                completed_percent = 0
                canceled_percent = 0

                if total_assigned > 0:
                    completed_percent = round((completed / total_assigned) * 100)
                    canceled_percent = round((canceled / total_assigned) * 100)

                return f"""📊 Статистика заказов:
                    • Взял {total_assigned}
                    • Выполнил {completed} ({completed_percent}%)
                    • Отказался {canceled} ({canceled_percent}%)"""

    except Exception as e:
        logger.error(f"Ошибка при получении статистики для пользователя {user_id}: {e}")
        return """📊 Статистика заказов:
            • Взял 0
            • Выполнил 0 (0%)
            • Отказался 0 (0%)"""


def dell_to_assigned_performers(user_id: int, id_tasks: int) -> str:
    """Удаляет пользователя из списка исполнителей задачи
    и обновляет статистику отказов"""
    if not isinstance(id_tasks, int):
        return "Некорректный номер задачи"

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Проверяем существование задачи
                cursor.execute("SELECT id_tasks FROM tasks WHERE id_tasks = %s", (id_tasks,))
                if not cursor.fetchone():
                    return "Задача не найдена"

                # Получаем данные задачи
                cursor.execute("""
                    SELECT task_status, required_workers, assigned_performers
                    FROM tasks 
                    WHERE id_tasks = %s
                """, (id_tasks,))
                task_data = cursor.fetchone()

                task_status = task_data[0]
                assigned_performers = task_data[2] if task_data[2] else []

                # Проверяем, что пользователь есть в списке исполнителей
                if user_id not in assigned_performers:
                    return "Вы не были назначены на эту задачу"

                # Проверяем статус задачи
                if task_status == 'Завершено':
                    return "Нельзя отказаться от завершенной задачи"
                elif task_status == 'Отменено':
                    return "Задача уже отменена"

                # Удаляем пользователя из списка исполнителей
                new_performers = [pid for pid in assigned_performers if pid != user_id]
                cursor.execute("""
                    UPDATE tasks 
                    SET assigned_performers = %s,
                        task_status = CASE 
                            WHEN %s = 'Работники найдены' THEN 'Назначена'
                            ELSE task_status
                        END
                    WHERE id_tasks = %s
                """, (new_performers if new_performers else None, task_status, id_tasks))

                # Удаляем запись из таблицы связей
                cursor.execute("""
                    DELETE FROM task_performers 
                    WHERE task_id = %s AND id_user_telegram = %s
                """, (id_tasks, user_id))

                # Обновляем статистику исполнителя (увеличиваем счетчик отмененных задач)
                cursor.execute("""
                    INSERT INTO performer_stats (id_user_telegram, canceled)
                    VALUES (%s, 1)
                    ON CONFLICT (id_user_telegram) 
                    DO UPDATE SET 
                        canceled = performer_stats.canceled + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (user_id,))

                return (f"Вы отказались от задачи {id_tasks}. "
                        f"Ваш рейтинг понижен.")

    except Exception as e:
        return f"Произошла ошибка: {str(e)}"


def complete_the_task_database(task_text: str) -> str:
    """Завершает задачу и обновляет статистику исполнителей"""
    try:
        # Проверяем, что передан номер задачи (число)
        if not task_text.isdigit():
            return "Номер задачи должен быть числом"

        id_tasks = int(task_text)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Проверяем существование задачи
                cursor.execute("""
                    SELECT id_tasks, assigned_performers 
                    FROM tasks 
                    WHERE id_tasks = %s
                """, (id_tasks,))

                task_data = cursor.fetchone()
                if not task_data:
                    return "Задача не найдена"

                # 2. Обновляем статус задачи
                cursor.execute("""
                    UPDATE tasks 
                    SET task_status = 'Завершено' 
                    WHERE id_tasks = %s
                """, (id_tasks,))

                # 3. Получаем список исполнителей
                assigned_performers = task_data[1] if task_data[1] else []

                if assigned_performers:
                    # 4. Обновляем статистику для каждого исполнителя
                    for performer_id in assigned_performers:
                        cursor.execute("""
                            INSERT INTO performer_stats (id_user_telegram, completed)
                            VALUES (%s, 1)
                            ON CONFLICT (id_user_telegram) 
                            DO UPDATE SET 
                                completed = performer_stats.completed + 1,
                                last_updated = CURRENT_TIMESTAMP
                        """, (performer_id,))

                return f"Задача {id_tasks} успешно завершена. Исполнителям добавлено + 1 в карму."

    except Exception as e:
        return f"Ошибка при завершении задачи: {str(e)}"


async def delete_the_task_database(task_text: str, bot: Bot = None) -> str:
    """Удаляет задачу, корректирует статистику и уведомляет исполнителей"""
    try:
        # Проверяем, что передан номер задачи (число)
        if not task_text.isdigit():
            return "❌ Номер задачи должен быть числом"

        id_tasks = int(task_text)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Получаем данные задачи перед удалением
                cursor.execute("""
                    SELECT assigned_performers, task_type 
                    FROM tasks 
                    WHERE id_tasks = %s
                """, (id_tasks,))

                task_data = cursor.fetchone()
                if not task_data:
                    return f"❌ Задача {id_tasks} не найдена"

                assigned_performers = task_data[0] if task_data[0] else []
                task_type = task_data[1]  # 'Погрузка' или 'Доставка'

                # 2. Уменьшаем счетчики у исполнителей (если они есть)
                if assigned_performers:
                    for performer_id in assigned_performers:
                        cursor.execute("""
                            UPDATE performer_stats 
                            SET total_assigned = GREATEST(0, total_assigned - 1),
                                last_updated = CURRENT_TIMESTAMP
                            WHERE id_user_telegram = %s
                        """, (performer_id,))

                # 3. Удаляем задачу
                cursor.execute("""
                    DELETE FROM tasks 
                    WHERE id_tasks = %s
                    RETURNING id_tasks
                """, (id_tasks,))

                if not cursor.fetchone():
                    return f"❌ Не удалось удалить задачу {id_tasks}"

                # 4. Уведомляем всех исполнителей соответствующего типа
                if bot:
                    user_type = 'грузчиков' if task_type == 'Погрузка' else 'водителей'
                    notification = f"🔔 Задача {id_tasks} ({task_type}) была удалена администратором"

                    # Получаем всех активных исполнителей этого типа
                    performer_ids = get_all_users_type(task_type)

                    for user_id in performer_ids:
                        try:
                            await bot.send_message(user_id, notification)
                        except Exception as e:
                            print(f"Не удалось уведомить пользователя {user_id}: {e}")

                return f"✅ Задача {id_tasks} удалена. Уведомлены все {user_type}."

    except Exception as e:
        logger.error(f"Ошибка при удалении задачи {task_text}: {str(e)}")
        return f"❌ Ошибка при удалении задачи: {str(e)}"


def all_order_admin_database() -> str:
    """Возвращает форматированную информацию о всех активных задачах"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Получаем все активные задачи
                cursor.execute("""
                    SELECT 
                        id_tasks, 
                        created_at,
                        assignment_date,
                        assignment_time,
                        task_type,
                        description,
                        main_address,
                        additional_address,
                        required_workers,
                        worker_price,
                        assigned_performers,
                        task_status
                    FROM tasks
                    WHERE task_status IN ('Назначена', 'Работники найдены')
                    ORDER BY assignment_date, assignment_time
                """)

                tasks = cursor.fetchall()

                if not tasks:
                    return "ℹ️ Активных задач не найдено"

                result = []
                for task in tasks:
                    # Получаем информацию о назначенных исполнителях
                    assigned_performers = []
                    if task[10]:  # Если есть assigned_performers
                        cursor.execute("""
                            SELECT id_user_telegram, first_name, last_name, phone
                            FROM users
                            WHERE id_user_telegram = ANY(%s)
                        """, (task[10],))
                        assigned_performers = cursor.fetchall()

                    # Форматируем информацию о задаче
                    task_info = (
                        f"🔹 Номер задачи: {task[0]}\n"
                        f"📅 Дата создания: {task[1].strftime('%d.%m.%Y %H:%M')}\n"
                        f"📆 Дата выполнения: {task[2] if task[2] else 'Не указана'}\n"
                        f"⏰ Время: {task[3] if task[3] else 'Не указано'}\n"
                        f"🏷 Тип: {task[4]}\n"
                        f"📝 Описание: {task[5]}\n"
                        f"🏠 Адрес: {task[6]}\n"
                        f"🏡 Доп. адрес: {task[7] if task[7] else 'Нет'}\n"
                        f"👷 Требуется работников: {task[8]}\n"
                        f"💰 Цена за работу: {task[9]} руб.\n"
                        f"📊 Статус: {task[11]}\n"
                    )

                    # Форматируем информацию о назначенных исполнителях
                    if assigned_performers:
                        performers_info = "\n👥 Назначенные исполнители:\n"
                        for performer in assigned_performers:
                            performers_info += (
                                f"  👤 {performer[1]} {performer[2]} "
                                f"(ID: {performer[0]}, 📞 {performer[3]})\n"
                            )
                        task_info += performers_info
                    else:
                        task_info += "\n⚠️ Исполнители еще не назначены\n"

                    result.append(task_info)

                return "\n\n".join(result)

    except Exception as e:
        logger.error(f"Ошибка при получении списка задач: {str(e)}")
        return "❌ Произошла ошибка при получении списка задач"
