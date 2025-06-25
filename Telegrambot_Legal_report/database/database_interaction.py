import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


class DatabaseInteraction:
    def __init__(self):
        """
        Инициализирует соединение с базой данных PostgreSQL.
        Использует параметры из переменных окружения.
        """
        self.conn = psycopg2.connect(
            host=os.getenv('HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        self.cursor = self.conn.cursor()

    def user_exists(self, user_id: int) -> bool:
        """
        Проверяет наличие пользователя в базе данных по ID Telegram.

        :param user_id: ID пользователя в Telegram
        :return: True если пользователь существует, False если нет
        """
        query = "SELECT 1 FROM users WHERE id_user_telegram = %s"
        self.cursor.execute(query, (user_id,))
        return bool(self.cursor.fetchone())

    def get_user_status(self, user_id: int) -> str:
        self.cursor.execute("SELECT status FROM users WHERE telegram_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 'Неизвестен'

    def get_user_status(self, user_id: int) -> str:
        self.cursor.execute("SELECT status FROM users WHERE id_user_telegram = %s", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 'Неизвестен'

    def is_admin(self, user_id):
        """
        Проверяет, является ли пользователь администратором.

        :param user_id: ID пользователя в Telegram
        :return: True если пользователь является администратором, False если нет
        """
        return str(user_id) == os.getenv('ADMIN')

    def add_user(self, user_id, first_name, last_name):
        """
        Добавляет нового пользователя в базу данных.
        Если пользователь уже существует, не производит никаких действий.

        :param user_id: ID пользователя в Telegram
        :param first_name: Имя пользователя
        :param last_name: Фамилия пользователя
        """
        query = """
        INSERT INTO users (id_user_telegram, first_name, last_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id_user_telegram) DO NOTHING
        """
        self.cursor.execute(query, (user_id, first_name, last_name))
        self.conn.commit()

    def update_user_status(self, user_id, status):
        """
        Обновляет статус пользователя в базе данных.

        :param user_id: ID пользователя в Telegram
        :param status: Новый статус пользователя
        """
        query = """
        UPDATE users
        SET status = %s
        WHERE id_user_telegram = %s
        """
        self.cursor.execute(query, (status, user_id))
        self.conn.commit()

    def get_blocked_users(self):
        """
        Возвращает список всех заблокированных пользователей.

        :return: Список кортежей с данными пользователей (id, имя, фамилия)
        """
        query = """
        SELECT id_user_telegram, first_name, last_name 
        FROM users 
        WHERE status = 'Заблокированный'
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_active_users(self):
        """
        Возвращает список всех активных пользователей.

        :return: Список кортежей с данными пользователей (id, имя, фамилия)
        """
        query = """
        SELECT id_user_telegram, first_name, last_name 
        FROM users 
        WHERE status = 'Активный'
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        """
        Закрывает соединение с базой данных.
        Всегда вызывайте этот метод при завершении работы с классом.
        """
        self.cursor.close()
        self.conn.close()