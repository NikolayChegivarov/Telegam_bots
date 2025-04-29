import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import os


from config import Config

def get_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        port=Config.DB_PORT
    )


def connect_to_database(dbname=None):
    """Функция устанавливает подключение к базе данных указанной в аргументе."""
    if dbname is None:
        dbname = os.getenv("NAME_DB")
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=dbname if dbname else os.getenv("NAME_DB"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD_DB"),
            port=os.getenv("PORT")
        )
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при подключении к PostgreSQL: {error}")
        return None

def check_and_create_db():
    """Проверка наличия базы данных и её создание, если она отсутствует."""
    connection = None
    cursor = None
    try:
        connection = connect_to_database(dbname="postgres")  # Подключение к стандартной базе данных
        if not connection:
            return False

        connection.autocommit = True
        cursor = connection.cursor()

        # Проверка наличия базы данных
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [os.getenv("NAME_DB")])
        exists = cursor.fetchone()

        if not exists:
            # Создание базы данных, если она отсутствует
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(os.getenv("NAME_DB"))))
            print(f"База данных {os.getenv('NAME_DB')} успешно создана.")
        else:
            print(f"База данных {os.getenv('NAME_DB')} уже существует.")

        return True
    except Exception as e:
        print(f"Ошибка при проверке или создании базы данных: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def initialize_database():
    """Функция для инициализации базы данных, включая создание таблиц, если они отсутствуют."""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            return False

        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id_user_telegram BIGINT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,                              -- Имя
                last_name VARCHAR(50) NOT NULL,                               -- Фамилия
                phone VARCHAR(20) NOT NULL,                                   -- Телефон
                is_loader BOOLEAN NOT NULL DEFAULT FALSE,                     -- Грузчик
                is_driver BOOLEAN NOT NULL DEFAULT FALSE,                     -- Водитель
                is_self_employed BOOLEAN NOT NULL DEFAULT FALSE,              -- Самозанятый
                inn VARCHAR(12) NULL,                                         -- ИНН
                status VARCHAR(20) NOT NULL                                   -- Статус активности
                    DEFAULT 'Заблокированный'
                    CHECK (status IN ('Активный', 'Заблокированный')),
                comment TEXT NULL,                                            -- Комментарий администратора
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP       -- Когда создан
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id_tasks BIGSERIAL PRIMARY KEY, 
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,      -- Дата, время создания задачи
                assignment_date DATE NULL,                                    -- Дата назначения
                assignment_time TIME NULL,                                    -- Время назначения
                task_type VARCHAR(20) NOT NULL                                -- Тип задачи
                    CHECK (task_type IN ('Погрузка', 'Доставка')),            
                description TEXT NOT NULL,                                    -- Описание
                main_address VARCHAR(200) NOT NULL,                           -- Адрес основной
                additional_address VARCHAR(200) NULL,                         -- Адрес дополнительный
                required_workers INT NOT NULL,                                -- Количество необходимых работников
                worker_price NUMERIC(10, 2) NOT NULL,                         -- Цена за работу
                assigned_performers BIGINT[] NULL,                            -- Назначенные исполнители
                task_status VARCHAR(30) NOT NULL                              -- Статус задачи
                    DEFAULT 'Назначена'
                    CHECK (task_status IN ('Назначена', 'Работники найдены', 'Завершено', 'Отменено'))
            );
            CREATE TABLE IF NOT EXISTS performer_stats (
                id_user_telegram BIGINT PRIMARY KEY REFERENCES users(id_user_telegram),
                total_assigned INT NOT NULL DEFAULT 0,                        -- Всего назначено
                completed INT NOT NULL DEFAULT 0,                             -- Успешно выполнено
                canceled INT NOT NULL DEFAULT 0,                              -- Отказано/отменено
                last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS task_performers (                      -- Связи
                task_id BIGINT NOT NULL,
                id_user_telegram BIGINT NOT NULL,
                PRIMARY KEY (task_id, id_user_telegram),                      -- одна и та же комбинация задачи и пользователя не может повторяться
                FOREIGN KEY (task_id) REFERENCES tasks(id_tasks) ON DELETE CASCADE,  -- Если удаляется задача или пользователь, все связанные записи в этой таблице автоматически удаляются.
                FOREIGN KEY (id_user_telegram) REFERENCES users(id_user_telegram) ON DELETE CASCADE
            );
        """)
        connection.commit()
        print("Таблицы успешно созданы или уже существует.")
        return True
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Ошибка при создании таблицы: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def add_user_to_database(user_id):
    """Добавляет пользователя бд"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            print("Не удалось подключиться к базе данных")
            return False

        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (user_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO users 
                (id_user_telegram, first_name, last_name, phone, is_loader, is_driver, 
                 is_self_employed, inn, status, comment)
                VALUES 
                (%s, '', '', '', FALSE, FALSE, FALSE, NULL, 'Заблокированный', NULL)
            """, (user_id,))
            connection.commit()
            print(f"Пользователь {user_id} добавлен в базу данных")
            return True
        print(f"Пользователь {user_id} уже существует")
        return False

    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def status_verification(user_id):
    """Проверка пользователя на статус 'Активный'"""
    connection = connect_to_database()
    if not connection:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT status FROM users WHERE id_user_telegram = %s", (user_id,))
        result = cursor.fetchone()
        return result and result[0] == "Активный"
    except Exception as e:
        print(f"Ошибка при проверке статуса: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

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
    """Функция администратора, для изменения статуса пользователя на 'Активный'"""
    connection = None
    cursor = None
    try:
        connection = connect_to_database()
        if not connection:
            print("Не удалось подключиться к базе данных")
            return False

        cursor = connection.cursor()

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (user_id,))
        exists = cursor.fetchone()

        if exists:
            # Обновляем статус пользователя
            cursor.execute("""
                UPDATE users 
                SET status = 'Активный'
                WHERE id_user_telegram = %s
            """, (user_id,))

            connection.commit()
            print(f"Статус пользователя {user_id} изменен на 'Активный'")
            return True
        else:
            print(f"Пользователь {user_id} не найден в базе данных")
            return False

    except Exception as e:
        print(f"Ошибка при изменении статуса пользователя: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_task(task_data: dict) -> int:
    """
    Создает новую задачу в базе данных
    :param task_data: Словарь с данными задачи (включая worker_price)
    :return: ID созданной задачи
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

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
            task_data['additional_address'],
            task_data['required_workers'],
            task_data['worker_price'],  # Используем переданную цену
            'Назначена'
        ))

        task_id = cursor.fetchone()[0]
        connection.commit()
        return task_id
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Ошибка при создании задачи: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_all_users_type(task_type: str = None):
    """
    Получает список пользователей из базы данных для заданной роли
    :param task_type: Тип задачи ('Погрузка' или 'Доставка')
    :return: Список ID пользователей
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT id_user_telegram 
            FROM users 
            WHERE status = 'Активный'
        """
        params = []

        # Добавляем фильтр по роли в зависимости от типа задачи
        if task_type == 'Погрузка':
            query += " AND is_loader = TRUE"
        elif task_type == 'Доставка':
            query += " AND is_driver = TRUE"
        else:
            # Если тип задачи не указан или не распознан, возвращаем всех активных пользователей
            pass

        cursor.execute(query, params)
        user_ids = [row[0] for row in cursor.fetchall()]
        return user_ids

    except Exception as e:
        print(f"Ошибка при получении пользователей: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_pending_tasks(user_type: str = None) -> list[dict]:
    """
    Получает все задачи со статусом 'Назначена' из базы данных
    с фильтрацией по типу задачи, если указан тип пользователя

    Параметры:
        user_type: str - тип пользователя ('loader' или 'driver')

    Возвращает список словарей с информацией о задачах
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        query = """
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
            {type_condition}
            ORDER BY assignment_date, assignment_time
        """

        type_condition = ""
        if user_type == "loader":
            type_condition = "AND task_type = 'Погрузка'"
        elif user_type == "driver":
            type_condition = "AND task_type = 'Доставка'"

        query = query.format(type_condition=type_condition)

        cursor.execute(query)
        tasks = []

        for row in cursor.fetchall():
            task = {
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
            tasks.append(task)

        return tasks

    except Exception as e:
        print(f"Ошибка при получении задач: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


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
    """Получить данные пользователя по его ID в Telegram с красивым оформлением"""
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

