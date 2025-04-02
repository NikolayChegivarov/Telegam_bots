from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import connect_to_database
from keyboards import get_cancel_kb, get_admin_kb
import logging
from utils import is_admin

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == '➕ Добавить услугу')
async def add_service(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    await message.answer("Введите название услуги:")
    await state.set_state(AdminStates.waiting_for_service_name)


class AdminStates(StatesGroup):
    waiting_for_master_id = State()
    waiting_for_service_name = State()
    waiting_for_service_price = State()
    waiting_for_service_duration = State()


async def check_admin(message: Message):
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM users 
                WHERE id_user_telegram = %s AND id_user_type = 3
            """, (message.from_user.id,))
            return bool(cursor.fetchone())
    finally:
        conn.close()


@router.message(F.text == '👨‍💼 Добавить мастера')
async def add_master(message: Message, state: FSMContext):
    if not await check_admin(message):
        await message.answer("Эта команда доступна только администраторам.")
        return

    await message.answer("Введите ID пользователя Telegram, которого хотите сделать мастером:",
                         reply_markup=get_cancel_kb())
    await state.set_state(AdminStates.waiting_for_master_id)


@router.message(AdminStates.waiting_for_master_id)
async def process_master_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите числовой ID пользователя.")
        return

    master_id = int(message.text)
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (master_id,))
            if not cursor.fetchone():
                await message.answer("Пользователь с таким ID не найден. Попросите его сначала запустить бота.")
                await state.clear()
                return

            cursor.execute(
                "UPDATE users SET id_user_type = 2 WHERE id_user_telegram = %s",
                (master_id,)
            )
            conn.commit()
            await message.answer(f"Пользователь {master_id} теперь мастер!", reply_markup=get_admin_kb())

            try:
                await message.bot.send_message(
                    master_id,
                    "Поздравляем! Администратор назначил вас мастером в нашем салоне красоты. "
                    "Теперь у вас есть доступ к панели мастера."
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить мастера {master_id}: {e}")
    finally:
        conn.close()
    await state.clear()


def register_admin_handlers(dp):
    dp.include_router(router)
