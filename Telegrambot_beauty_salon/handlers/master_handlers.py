from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import connect_to_database
from keyboards import get_master_main_menu, get_cancel_kb

router = Router()


class MasterStates(StatesGroup):
    waiting_for_specialization = State()
    waiting_for_photo = State()
    waiting_for_comment = State()


@router.message(F.text == '💼 Мой профиль')
async def show_master_profile(message: Message):
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.first_name, u.last_name, u.phone, u.specialization, u.my_comment, s.status_user 
                FROM users u
                JOIN status s ON u.id_status = s.id_status
                WHERE u.id_user_telegram = %s
            """, (message.from_user.id,))
            master = cursor.fetchone()

            if master:
                text = f"👤 Ваш профиль мастера:\n\nИмя: {master[0]}\nФамилия: {master[1]}\nТелефон: {master[2] or 'не указан'}\n"
                text += f"Специализация: {master[3] or 'не указана'}\nО себе: {master[4] or 'не указано'}\nСтатус: {master[5]}"
                await message.answer(text)
            else:
                await message.answer("Профиль не найден.")
    finally:
        conn.close()


def register_master_handlers(dp):
    dp.include_router(router)
