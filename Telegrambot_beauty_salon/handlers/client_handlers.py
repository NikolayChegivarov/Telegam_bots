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


@router.callback_query(F.data.startswith('master_'))
async def master_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора мастера"""
    try:
        master_id = int(callback.data.split('_')[1])
        await state.update_data(master_id=master_id)

        # Генерируем доступные даты (завтра + 13 дней)
        today = datetime.now().date()
        dates = [
            (today + timedelta(days=i)).strftime('%d.%m.%Y')
            for i in range(1, 14)
        ]

        await callback.message.edit_text(
            "Выберите дату:",
            reply_markup=get_dates_kb(dates)
        )
        await state.set_state(ClientStates.waiting_for_date)
    except Exception as e:
        logger.error(f"Ошибка выбора мастера: {e}")
        await callback.message.answer("Произошла ошибка, попробуйте снова")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith('date_'))
async def date_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    try:
        date_str = callback.data.split('_')[1]
        selected_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        await state.update_data(date=selected_date)

        # Генерируем доступное время
        times = [f"{hour}:00" for hour in range(10, 19)]  # с 10:00 до 18:00

        await callback.message.edit_text(
            "Выберите время:",
            reply_markup=get_times_kb(times)
        )
        await state.set_state(ClientStates.waiting_for_time)
    except Exception as e:
        logger.error(f"Ошибка выбора даты: {e}")
        await callback.message.answer("Произошла ошибка, попробуйте снова")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith('time_'))
async def time_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    try:
        time_str = callback.data.split('_')[1]
        selected_time = datetime.strptime(time_str, '%H:%M').time()
        data = await state.get_data()

        # Проверяем доступность времени
        conn = connect_to_database()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 FROM record 
                    WHERE id_master = %s AND date = %s AND time = %s
                """, (data['master_id'], data['date'], selected_time))

                if cursor.fetchone():
                    await callback.message.answer("Это время уже занято, выберите другое")
                    return

                # Получаем данные для подтверждения
                cursor.execute("""
                    SELECT s.name, s.price, u.first_name, u.last_name
                    FROM services s, users u
                    WHERE s.id_services = %s AND u.id_user_telegram = %s
                """, (data['service_id'], data['master_id']))
                service_name, price, master_first, master_last = cursor.fetchone()

                # Сохраняем все данные в состояние
                await state.update_data({
                    'service_name': service_name,
                    'price': price,
                    'time': selected_time,
                    'time_str': time_str
                })

                confirmation_text = (
                    f"Подтвердите запись:\n\n"
                    f"🔹 Услуга: {service_name}\n"
                    f"💰 Цена: {price} руб.\n"
                    f"👨‍🔧 Мастер: {master_first} {master_last}\n"
                    f"📅 Дата: {data['date'].strftime('%d.%m.%Y')}\n"
                    f"⏰ Время: {time_str}"
                )

                await callback.message.edit_text(
                    confirmation_text,
                    reply_markup=get_confirm_appointment_kb(
                        data['service_id'],
                        data['master_id'],
                        data['date'],
                        selected_time
                    )
                )
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка выбора времени: {e}")
        await callback.message.answer("Произошла ошибка, попробуйте снова")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith('confirm_'))
async def confirm_appointment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    try:
        _, service_id, master_id, date_str, time_str = callback.data.split('_')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        selected_time = datetime.strptime(time_str, '%H:%M').time()

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

                await callback.message.edit_text(
                    "✅ Запись успешно оформлена!",
                    reply_markup=None
                )
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка подтверждения записи: {e}")
        await callback.message.answer("Произошла ошибка при записи")
    finally:
        await state.clear()
        await callback.answer()


@router.callback_query(F.data == 'cancel_appointment')
async def handle_cancellation(callback: CallbackQuery, state: FSMContext):
    """Обработка отмены записи"""
    await callback.message.edit_text(
        "Запись отменена",
        reply_markup=None
    )
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