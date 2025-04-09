from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from yookassa import Payment
import logging
from database import connect_to_database
from datetime import datetime

from keyboards import get_payment_check_kb

router = Router()
logger = logging.getLogger(__name__)


async def save_appointment_to_db(data):
    """Сохранение записи в БД и возврат appointment_id"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO record 
                (id_service, id_client, id_master, date, time) 
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_record
            """, (
                data['service_id'],
                data['user_id'],
                data['master_id'],
                data['date'],
                data['time']
            ))
            appointment_id = cursor.fetchone()[0]
            conn.commit()
            return appointment_id
    finally:
        conn.close()


async def save_payment_to_db(appointment_id, payment_id, amount):
    """Сохранение платежа в БД"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO payments 
                (payment_id, id_record, amount, status) 
                VALUES (%s, %s, %s, 'pending')
            """, (payment_id, appointment_id, amount))
            conn.commit()
    finally:
        conn.close()


async def update_payment_status(payment_id, status):
    """Обновление статуса платежа"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE payments 
                SET status = %s, 
                    paid_at = CASE WHEN %s = 'paid' THEN NOW() ELSE paid_at END
                WHERE payment_id = %s
            """, (status, status, payment_id))
            conn.commit()
    finally:
        conn.close()


@router.callback_query(F.data.startswith('payment_'))
async def confirm_appointment_with_payment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение записи с созданием платежа"""
    try:
        # Получаем все данные из состояния
        data = await state.get_data()

        # Проверяем наличие всех необходимых данных
        required_fields = ['service_id', 'master_id', 'date', 'time', 'service_name', 'price']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field in state: {field}")

        # Сохраняем запись
        appointment_id = await save_appointment_to_db({
            'service_id': data['service_id'],
            'user_id': callback.from_user.id,
            'master_id': data['master_id'],
            'date': data['date'],
            'time': data['time']
        })

        # Создаем платеж в ЮKassa
        payment = Payment.create({
            "amount": {
                "value": str(data['price']),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/your_bot"
            },
            "description": f"Услуга: {data['service_name']}",
            "metadata": {
                "user_id": callback.from_user.id,
                "appointment_id": appointment_id
            },
            "capture": True
        })

        # Сохраняем платеж
        await save_payment_to_db(appointment_id, payment.id, data['price'])

        await callback.message.answer(
            f"💳 Для завершения записи оплатите {data['price']} руб.\n"
            "Ссылка действительна 24 часа:",
            reply_markup=get_payment_check_kb(payment.id)
        )

    except Exception as e:
        logger.error(f"Payment error: {e}")
        await callback.message.answer("Ошибка при создании платежа. Попробуйте позже.")
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith('check_payment_'))
async def check_payment_status(callback: CallbackQuery):
    """Проверка статуса платежа"""
    payment_id = callback.data.split('_')[-1]
    try:
        payment = Payment.find_one(payment_id)

        if payment.status == 'succeeded':
            await update_payment_status(payment_id, 'paid')
            await callback.message.edit_text(
                "✅ Оплата подтверждена! Ждем вас в салоне.",
                reply_markup=None
            )
        else:
            await callback.answer("Оплата еще не поступила", show_alert=True)

    except Exception as e:
        logger.error(f"Payment check error: {e}")
        await callback.answer("Ошибка проверки платежа", show_alert=True)


def register_payment_handlers(dp):
    dp.include_router(router)
