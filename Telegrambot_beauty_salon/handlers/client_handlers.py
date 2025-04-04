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
    waiting_for_service = State()
    waiting_for_master = State()
    waiting_for_date = State()
    waiting_for_time = State()


# Вспомогательные функции
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


# Обработчики записи на услугу
@router.message(F.text == '📅 Записаться на услугу')
async def start_appointment_process(message: Message, state: FSMContext):
    """Начало процесса записи на услугу"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            # Запрашиваем все необходимые поля для клавиатуры
            cursor.execute("SELECT id_services, name, price, duration FROM services")
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
        for i in range(1, 15)
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
    """Обработка выбора услуги"""
    service_id = int(callback.data.split('_')[1])
    await state.update_data(service_id=service_id)

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            # Получаем информацию об услуге
            cursor.execute("SELECT name, price, duration FROM services WHERE id_services = %s", (service_id,))
            service = cursor.fetchone()

            if service:
                # Получаем список доступных мастеров для этой услуги
                cursor.execute("""
                    SELECT id_user_telegram, first_name, last_name 
                    FROM users 
                    WHERE id_user_type = 2 AND id_status = 1
                """)
                masters = cursor.fetchall()

                if masters:
                    await callback.message.answer(
                        f"Вы выбрали услугу: <b>{service[0]}</b>\n"
                        f"💰 Цена: {service[1]} руб.\n"
                        f"⏱ Длительность: {service[2]} мин.\n\n"
                        "Теперь выберите мастера:",
                        reply_markup=get_masters_kb(masters)
                    )
                    await state.set_state(ClientStates.waiting_for_master)
                else:
                    await callback.message.answer("Нет доступных мастеров для этой услуги.")
            else:
                await callback.message.answer("Услуга не найдена.")
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