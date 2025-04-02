from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import connect_to_database
from keyboards import get_client_main_menu, get_cancel_kb, get_services_kb, get_confirm_appointment_kb

# Инициализация роутера
router = Router()


class ClientStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_service = State()
    waiting_for_date = State()
    waiting_for_time = State()


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
                text = f"👤 Ваш профиль:\n\nИмя: {user[0]}\nФамилия: {user[1]}\nТелефон: {user[2] or 'не указан'}\nСтатус: {user[3]}"
                await message.answer(text)
            else:
                await message.answer("Профиль не найден.")
    finally:
        conn.close()


@router.message(F.text == '📱 Изменить телефон')
async def request_phone(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, введите ваш телефонный номер:", reply_markup=get_cancel_kb())
    await state.set_state(ClientStates.waiting_for_phone)


@router.message(ClientStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text
    if not phone.replace('+', '').isdigit():
        await message.answer("Пожалуйста, введите корректный номер телефона.")
        return

    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET phone = %s WHERE id_user_telegram = %s",
                (phone, message.from_user.id)
            )
            conn.commit()
            await message.answer("Номер телефона успешно сохранён!", reply_markup=get_client_main_menu())
    finally:
        conn.close()
    await state.clear()


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
