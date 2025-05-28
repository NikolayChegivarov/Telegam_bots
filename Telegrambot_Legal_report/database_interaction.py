import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


class DatabaseInteraction:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        self.cursor = self.conn.cursor()

    def check_user_status(self, user_id):
        """Проверяет статус пользователя в базе данных."""
        query = "SELECT status FROM users WHERE id_user_telegram = %s"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def is_admin(self, user_id):
        """Проверяет, является ли пользователь администратором."""
        return str(user_id) == os.getenv('ADMIN')

    def add_user(self, user_id, first_name, last_name):
        """Добавляет нового пользователя в базу данных."""
        query = """
        INSERT INTO users (id_user_telegram, first_name, last_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id_user_telegram) DO NOTHING
        """
        self.cursor.execute(query, (user_id, first_name, last_name))
        self.conn.commit()

    def close(self):
        """Закрывает соединение с базой данных."""
        self.cursor.close()
        self.conn.close()

    def get_blocked_users(self):
        """Возвращает список заблокированных пользователей."""
        query = """
        SELECT id_user_telegram, first_name, last_name 
        FROM users 
        WHERE status = 'Заблокированный'
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def update_user_status(self, user_id, status):
        """Обновляет статус пользователя."""
        query = """
        UPDATE users
        SET status = %s
        WHERE id_user_telegram = %s
        """
        self.cursor.execute(query, (status, user_id))
        self.conn.commit()

    def get_active_users(self):
        """Возвращает список активных пользователей."""
        query = """
        SELECT id_user_telegram, first_name, last_name 
        FROM users 
        WHERE status = 'Активный'
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
