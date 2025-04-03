from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date, time, timedelta
from database import connect_to_database
from keyboards import (
    get_client_main_menu,
    get_cancel_kb,
    get_services_kb,
    get_confirm_appointment_kb,
    edit_profile_menu,
    get_masters_kb,
    get_dates_kb,
    get_times_kb
)
import re
import logging
from typing import Optional

# Инициализация логгера
logger = logging.getLogger(__name__)
router = Router()


class ClientStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()
    waiting_for_service = State()
    waiting_for_master = State()
    waiting_for_date = State()
    waiting_for_time = State()


# Вспомогательные функции
def is_valid_phone(phone: str) -> bool:
    """Проверка валидности номера телефона"""
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    if cleaned_phone.startswith('+'):
        return len(cleaned_phone) == 12 and cleaned_phone[1:].isdigit() and cleaned_phone[1] == '7'
    elif len(cleaned_phone) == 11:
        return cleaned_phone[0] in ('7', '8') and cleaned_phone.isdigit()
    return False


async def validate_date(date_str: str) -> Optional[date]:
    """Проверка и преобразование даты"""
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return None


async def validate_time(time_str: str) -> Optional[time]:
    """Проверка и преобразование времени"""
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return None


# Обработчики профиля
@router.message(F.text == '💼 Мой профиль')
async def show_client_profile(message: Message):
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


@router.message(F.text == '🔙 Назад')
async def back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("ООООсновное меню", reply_markup=get_client_main_menu())


@router.message(F.text == '✏️ Редактировать имя')
async def request_phone(message: Message, state: FSMContext):
    await message.answer("Пожалуйста введите ваше имя:", reply_markup=get_cancel_kb())
    await state.set_state(ClientStates.waiting_for_name)


@router.message(F.text == '✏️ Редактировать фамилию')
async def request_phone(message: Message, state: FSMContext):
    await message.answer("Пожалуйста введите вашу фамилию:", reply_markup=get_cancel_kb())
    await state.set_state(ClientStates.waiting_for_last_name)


@router.message(F.text == '📱 Изменить телефон')
async def request_phone(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, введите ваш телефонный номер:", reply_markup=get_cancel_kb())
    await state.set_state(ClientStates.waiting_for_phone)


@router.message(ClientStates.waiting_for_name)
async def update_name(message: Message, state: FSMContext):
    name = message.text
    if name == "❌ Отмена":
        await state.clear()
        await message.answer("Основное меню", reply_markup=get_client_main_menu())
        return
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


@router.message(ClientStates.waiting_for_last_name)
async def update_last_name(message: Message, state: FSMContext):
    last_name = message.text
    if last_name == "❌ Отмена":
        await state.clear()
        await message.answer("Основное меню", reply_markup=get_client_main_menu())
        return
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


@router.message(ClientStates.waiting_for_phone)
async def update_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if phone == "❌ Отмена":
        await state.clear()
        await message.answer("Основное меню", reply_markup=get_client_main_menu())
        return

    # Удаляем все нецифровые символы, кроме возможного плюса в начале
    cleaned_phone = re.sub(r'[^\d+]', '', phone)

    # Проверяем номер по более строгим критериям
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

    Номера без кода страны (9161234567) **НЕ** принимаются!
    """
    # Удаляем всё, кроме цифр и плюса
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


# Обработчики записи на услугу
@router.message(F.text == '📅 Записаться на услугу')
async def start_appointment_process(message: Message, state: FSMContext):
    """Начало процесса записи на услугу"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_services, name FROM services")
            services = cursor.fetchall()

            if services:
                await message.answer("Выберите услугу:", reply_markup=get_services_kb(services))
                await state.set_state(ClientStates.waiting_for_service)
            else:
                await message.answer("Список услуг пока пуст.")
    finally:
        conn.close()


@router.callback_query(ClientStates.waiting_for_service, F.data.startswith('service_'))
async def service_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги"""
    service_id = int(callback.data.split('_')[1])
    await state.update_data(service_id=service_id)

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_user_telegram, first_name, last_name 
                FROM users 
                WHERE id_user_type = 2 AND id_status = 1
            """)  # Мастера с активным статусом
            masters = cursor.fetchall()

            if masters:
                await callback.message.answer("Выберите мастера:", reply_markup=get_masters_kb(masters))
                await state.set_state(ClientStates.waiting_for_master)
            else:
                await callback.message.answer("Нет доступных мастеров.")
                await state.clear()
    finally:
        conn.close()
    await callback.answer()


@router.callback_query(ClientStates.waiting_for_master, F.data.startswith('master_'))
async def master_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора мастера"""
    master_id = int(callback.data.split('_')[1])
    await state.update_data(master_id=master_id)

    # Генерируем доступные даты (сегодня + 14 дней)
    today = datetime.now().date()
    dates = [
        (today + timedelta(days=i)).strftime('%d.%m.%Y')
        for i in range(1, 15)  # Следующие 14 дней
    ]

    await callback.message.answer("Выберите дату:", reply_markup=get_dates_kb(dates))
    await state.set_state(ClientStates.waiting_for_date)
    await callback.answer()


@router.callback_query(ClientStates.waiting_for_date, F.data.startswith('date_'))
async def date_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    date_str = callback.data.split('_')[1]
    selected_date = await validate_date(date_str)

    if not selected_date:
        await callback.message.answer("Неверный формат даты. Попробуйте еще раз.")
        return

    await state.update_data(date=selected_date)

    # Генерируем доступное время (с 10:00 до 20:00 с интервалом в 1 час)
    times = [f"{hour}:00" for hour in range(10, 20)]

    await callback.message.answer("Выберите время:", reply_markup=get_times_kb(times))
    await state.set_state(ClientStates.waiting_for_time)
    await callback.answer()


@router.callback_query(ClientStates.waiting_for_time, F.data.startswith('time_'))
async def time_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени и подтверждение записи"""
    time_str = callback.data.split('_')[1]
    selected_time = await validate_time(time_str)

    if not selected_time:
        await callback.message.answer("Неверный формат времени. Попробуйте еще раз.")
        return

    data = await state.get_data()
    service_id = data['service_id']
    master_id = data['master_id']
    selected_date = data['date']

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            # Проверяем доступность времени
            cursor.execute("""
                SELECT 1 FROM record 
                WHERE id_master = %s AND date = %s AND time = %s
            """, (master_id, selected_date, selected_time))

            if cursor.fetchone():
                await callback.message.answer("Это время уже занято. Пожалуйста, выберите другое.")
                return

            # Получаем информацию об услуге
            cursor.execute("SELECT name, price FROM services WHERE id_services = %s", (service_id,))
            service = cursor.fetchone()

            # Получаем информацию о мастере
            cursor.execute("SELECT first_name, last_name FROM users WHERE id_user_telegram = %s", (master_id,))
            master = cursor.fetchone()

            if service and master:
                confirmation_text = (
                    f"Подтвердите запись:\n\n"
                    f"🔹 Услуга: {service[0]}\n"
                    f"💵 Цена: {service[1]} руб.\n"
                    f"👨‍🔧 Мастер: {master[0]} {master[1]}\n"
                    f"📅 Дата: {selected_date.strftime('%d.%m.%Y')}\n"
                    f"⏰ Время: {selected_time.strftime('%H:%M')}"
                )

                await callback.message.answer(
                    confirmation_text,
                    reply_markup=get_confirm_appointment_kb(service_id, master_id, selected_date, selected_time)
                )
    finally:
        conn.close()
    await callback.answer()


@router.callback_query(F.data.startswith('confirm_'))
async def confirm_appointment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    _, service_id, master_id, date_str, time_str = callback.data.split('_')
    selected_date = await validate_date(date_str)
    selected_time = await validate_time(time_str)

    if not selected_date or not selected_time:
        await callback.message.answer("Ошибка данных. Пожалуйста, начните заново.")
        await state.clear()
        return

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO record 
                (id_service, id_client, id_master, date, time) 
                VALUES (%s, %s, %s, %s, %s)
            """, (
                int(service_id),
                callback.from_user.id,
                int(master_id),
                selected_date,
                selected_time
            ))
            conn.commit()

            await callback.message.answer(
                "✅ Запись успешно оформлена!",
                reply_markup=get_client_main_menu()
            )

            # Уведомление мастеру (можно реализовать через utils.notify_master_about_appointment)
    finally:
        conn.close()
    await state.clear()
    await callback.answer()


@router.message(F.text == '📋 Услуги и цены')
async def show_services(message: Message):
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_services, name, price, duration FROM services")
            services = cursor.fetchall()

            if services:
                await message.answer("Выберите услугу:", reply_markup=get_services_kb(services))
            else:
                await message.answer("Список услуг пока пуст.")
    finally:
        conn.close()


@router.callback_query(F.data.startswith('service_'))
async def service_selected(callback: CallbackQuery, state: FSMContext):
    """Эта функция обрабатывает выбор услуги пользователем через callback."""
    service_id = callback.data.split('_')[1]
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM services WHERE id_services = %s", (service_id,))
            service = cursor.fetchone()

            if service:
                service_info = (
                    f"<b>{service[1]}</b>\n"
                    f"💰 Цена: {service[2]} руб.\n"
                    f"⏱ Длительность: {service[3]} мин.\n\n"
                    f"Хотите записаться на эту услугу?"
                )
                await callback.message.answer(
                    service_info,
                    reply_markup=get_confirm_appointment_kb(service_id)
                )
    finally:
        conn.close()
    await callback.answer()


@router.message(F.text == '💇 Мои записи')
async def show_client_appointments(message: Message):
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.id_record, s.name, u.first_name, u.last_name, r.date, r.time 
                FROM record r
                JOIN services s ON r.id_service = s.id_services
                JOIN users u ON r.id_master = u.id_user_telegram
                WHERE r.id_client = %s AND r.date >= CURRENT_DATE
                ORDER BY r.date, r.time
            """, (message.from_user.id,))
            appointments = cursor.fetchall()

            if appointments:
                text = "📅 Ваши ближайшие записи:\n\n"
                for app in appointments:
                    text += f"🔹 {app[1]} у {app[2]} {app[3]}\n📅 {app[4].strftime('%d.%m.%Y')} в {app[5].strftime('%H:%M')}\n\n"
                await message.answer(text)
            else:
                await message.answer("У вас нет предстоящих записей.")
    finally:
        conn.close()


def register_client_handlers(dp):
    dp.include_router(router)
