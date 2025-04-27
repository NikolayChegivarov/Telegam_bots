from aiogram import Router, types
from aiogram.filters import Command

from database import add_user_to_database
from keyboards.executor_kb import executor_authorization_keyboard
from keyboards.admin_kb import get_admin_keyboard
from config import Config

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_id = user.id

    try:
        print("Попытка добавить пользователя в БД")
        add_user_to_database(user_id)

        print("Распределение")
        if message.from_user.id in Config.ADMINS:
            print("Вошел администратор.")
            await message.answer("Добро пожаловать, Администратор!",
                                 reply_markup=get_admin_keyboard())
        else:
            text = ("Приветствую вас в боте. Если вы занимаетесь погрузо-разгрузочными работами или доставкой грузов, "
                    "здесь вы сможете получать заказы.")
            await message.answer(text,
                                 reply_markup=executor_authorization_keyboard())
    except Exception as e:
        print(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка, попробуйте позже")
