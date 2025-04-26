from aiogram import Router, types
from aiogram.filters import Command

from database import add_user_to_database
from keyboards.executor_kb import get_executor_keyboard
from keyboards.admin_kb import get_admin_keyboard
from config import Config

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Делит пользователей на клиентов и администраторов."""
    user = message.from_user
    user_id = user.id
    first_name = user.first_name
    last_name = user.last_name if user.last_name else "Не указана"
    username = user.username if user.username else "Не указан"

    add_user_to_database(user_id)

    if message.from_user.id in Config.ADMINS:
        print("Вошел администратор.")
        await message.answer("Добро пожаловать, Администратор!",
                           reply_markup=get_admin_keyboard())
    else:
        text="Приветствую вас в боте. Если вы занимаетесь погрузо-разгрузочными работами или доставкой грузов, здесь вы сможете получать заказы."
        await message.answer(text,
                           reply_markup=get_executor_keyboard())
