from aiogram import Router, types
from aiogram.filters import Command

from keyboards.executor_kb import get_executor_keyboard
from keyboards.admin_kb import get_admin_keyboard
from config import Config

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Делит пользователей на клиентов и администраторов."""
    if message.from_user.id in Config.ADMINS:
        await message.answer("Добро пожаловать, Администратор!",
                           reply_markup=get_admin_keyboard())
    else:
        text="Приветствую вас в боте. Если вы занимаетесь погрузо-разгузочными работами или доставкой грузов, здесь вы сможете получать заказы."
        await message.answer(text,
                           reply_markup=get_executor_keyboard())
