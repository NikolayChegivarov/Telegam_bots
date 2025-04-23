from aiogram import Router, types
from aiogram.filters import Command

from keyboards.client_kb import get_client_keyboard
from keyboards.admin_kb import get_admin_keyboard
from config import Config

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Делит пользователей на клиентов и администраторов."""
    if message.from_user.id in Config.ADMINS:
        await message.answer("Добро пожаловать, Администратор",
                           reply_markup=get_admin_keyboard())
    else:
        await message.answer("Приветствую вас в боте для оплаты услуг",
                           reply_markup=get_client_keyboard())