from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import connect_to_database
from keyboards import get_client_main_menu, get_master_main_menu, get_admin_kb
# from dotenv import load_dotenv
import os

router = Router()


@router.message(F.text == '/start')
async def cmd_start(message: Message, state: FSMContext):
    """
    Обрабатывает команду /start и проверяет наличие пользователя в базе данных.

    - Подключается к базе данных и ищет пользователя по Telegram ID.
    - Если пользователь найден, проверяет его тип (Клиент, Мастер, Администратор) и
      отправляет соответствующее приветственное сообщение с меню.
    - Если пользователь не найден, автоматически регистрирует его как клиента
      и отправляет приветственное сообщение с клиентским меню.
    - Закрывает соединение с базой данных после выполнения запроса.

    Args:
        message (Message): Сообщение от пользователя.
        state (FSMContext): Контекст состояния FSM.
    """

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_user_type, s.status_user 
                FROM users u
                JOIN status s ON u.id_status = s.id_status
                WHERE u.id_user_telegram = %s
            """, (message.from_user.id,))
            user = cursor.fetchone()
            print(f"Пользователь - {user}")
            ADMINS = list(map(int, os.getenv("ADMIN", "").split(",")))
            user_info = message.from_user  # Получаем объект пользователя

            # Извлекаем нужную информацию
            user_id = user_info.id
            # first_name = user_info.first_name
            # last_name = user_info.last_name
            # username = user_info.username

            if user:
                if user[0] == 1:    # Клиент
                    await message.answer("Добро пожаловать в наш салон красоты!", reply_markup=get_client_main_menu())
                elif user[0] == 2:  # Мастер
                    await message.answer("Добро пожаловать в панель мастера!", reply_markup=get_master_main_menu())
                elif user[0] == 3:  # Админ
                    await message.answer("Панель администратора", reply_markup=get_admin_kb())
            elif user_id in ADMINS:
                cursor.execute(
                    "INSERT INTO users (id_user_telegram, first_name, last_name, id_user_type) VALUES (%s, %s, %s, 3)",
                    (message.from_user.id, message.from_user.first_name, message.from_user.last_name)
                )
                conn.commit()
                await message.answer("Панель администратора", reply_markup=get_admin_kb())
            else:
                cursor.execute(
                    "INSERT INTO users (id_user_telegram, first_name, last_name, id_user_type) VALUES (%s, %s, %s, 1)",
                    (message.from_user.id, message.from_user.first_name, message.from_user.last_name)
                )
                conn.commit()
                await message.answer("Добро пожаловать! Вы были автоматически зарегистрированы как клиент.",
                                     reply_markup=get_client_main_menu())
    finally:
        conn.close()


@router.message(F.text == '/help')
async def cmd_help(message: Message):
    await message.answer("""
    Список доступных команд:
    /start - Начать работу с ботом
    /help - Получить справку
    /profile - Управление профилем
    """)


def register_common_handlers(dp):
    dp.include_router(router)
