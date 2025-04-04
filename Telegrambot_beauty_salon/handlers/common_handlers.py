from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup  # Добавлен импорт StatesGroup
from database import connect_to_database
from keyboards import get_client_main_menu, get_master_main_menu, get_admin_kb, get_cancel_kb, edit_profile_menu
# from dotenv import load_dotenv
import os
import re
import logging

router = Router()
logger = logging.getLogger(__name__)


class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()


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


@router.message(F.text == '💼 Мой профиль')
async def show_profile(message: Message):
    """Показывает профиль пользователя"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.first_name, u.last_name, u.phone, s.status_user 
                FROM users u
                JOIN status s ON u.id_status = s.id_status
                WHERE u.id_user_telegram = %s
            """, (message.from_user.id,))
            user = cursor.fetchone()

            if user:
                text = f"👤 Ваш профиль:\n\nИмя: {user[0]}\nФамилия: {user[1]}\nТелефон: {user[2] or 'не указан'}"
                await message.answer(text, reply_markup=edit_profile_menu())
            else:
                await message.answer("Профиль не найден.")
    finally:
        conn.close()


cancel_filter = F.text.in_(["❌ Отмена", "🔙 Назад"])


@router.message(cancel_filter)
async def handle_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Основное меню", reply_markup=get_client_main_menu())


@router.message(F.text == '✏️ Редактировать имя')
async def request_name(message: Message, state: FSMContext):
    """Запрашивает новое имя пользователя"""
    await message.answer("Пожалуйста введите ваше имя:", reply_markup=get_cancel_kb())
    await state.set_state(ProfileStates.waiting_for_name)


@router.message(F.text == '✏️ Редактировать фамилию')
async def request_last_name(message: Message, state: FSMContext):
    """Запрашивает новую фамилию пользователя"""
    await message.answer("Пожалуйста введите вашу фамилию:", reply_markup=get_cancel_kb())
    await state.set_state(ProfileStates.waiting_for_last_name)


@router.message(F.text == '📱 Изменить телефон')
async def request_phone(message: Message, state: FSMContext):
    """Запрашивает новый телефон пользователя"""
    await message.answer("Пожалуйста, введите ваш телефонный номер:", reply_markup=get_cancel_kb())
    await state.set_state(ProfileStates.waiting_for_phone)


@router.message(ProfileStates.waiting_for_name)
async def update_name(message: Message, state: FSMContext):
    """Обновляет имя пользователя в базе данных"""
    name = message.text
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET first_name = %s WHERE id_user_telegram = %s",
                (name, message.from_user.id)
            )
            conn.commit()
            await message.answer("Вы успешно изменили имя в профиле!", reply_markup=get_client_main_menu())
    finally:
        conn.close()
    await state.clear()


@router.message(ProfileStates.waiting_for_last_name)
async def update_last_name(message: Message, state: FSMContext):
    """Обновляет фамилию пользователя в базе данных"""
    last_name = message.text
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET last_name = %s WHERE id_user_telegram = %s",
                (last_name, message.from_user.id)
            )
            conn.commit()
            await message.answer("Вы успешно изменили фамилию в профиле!", reply_markup=get_client_main_menu())
    finally:
        conn.close()
    await state.clear()


@router.message(ProfileStates.waiting_for_phone)
async def update_phone(message: Message, state: FSMContext):
    """Обновляет телефон пользователя в базе данных"""
    phone = message.text.strip()
    cleaned_phone = re.sub(r'[^\d+]', '', phone)

    if not is_valid_phone(cleaned_phone):
        await message.answer(
            "Пожалуйста, введите корректный номер телефона в международном формате.\n"
            "Пример: +79161234567 или 89161234567"
        )
        return

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET phone = %s WHERE id_user_telegram = %s",
                (cleaned_phone, message.from_user.id)
            )
            conn.commit()
            await message.answer("Номер телефона успешно сохранён!", reply_markup=get_client_main_menu())
    except Exception as e:
        await message.answer("Произошла ошибка при сохранении номера. Пожалуйста, попробуйте позже.")
        logger.error(f"Error saving phone number: {e}")
    finally:
        conn.close()
    await state.clear()


def is_valid_phone(phone: str) -> bool:
    """
    Строгая проверка российских номеров телефона.
    Допустимые форматы:
    - +79161234567 (обязательно 11 цифр после +7)
    - 89161234567 (обязательно 11 цифр, начинается с 8 или 7)
    - 79161234567 (обязательно 11 цифр)

    Номера без кода страны (9161234567) НЕ принимаются!
    """
    cleaned_phone = re.sub(r'[^\d+]', '', phone)

    # 1. Проверка международного формата (+7...)
    if cleaned_phone.startswith('+'):
        return (
                len(cleaned_phone) == 12  # +7 + 10 цифр
                and cleaned_phone[1:].isdigit()  # после + только цифры
                and cleaned_phone[1] == '7'  # код России
        )

    # 2. Проверка российского формата (8... или 7...)
    elif len(cleaned_phone) == 11:
        return (
                cleaned_phone[0] in ('7', '8')  # начинается с 7 или 8
                and cleaned_phone.isdigit()  # только цифры
        )

    # 3. Все остальные случаи (10 цифр, 9 цифр, буквы и т.д.) — невалидны
    return False


def register_common_handlers(dp):
    dp.include_router(router)