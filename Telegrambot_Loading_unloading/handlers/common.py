from aiogram import Router, types
from aiogram.filters import Command

from database import add_user_to_database, status_verification, checking_your_personal_account
from keyboards.executor_kb import executor_authorization_keyboard, acquaintance_keyboard, get_executor_keyboard
from keyboards.admin_kb import get_admin_keyboard
from config import Config

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_id = user.id

    try:
        print("Если пользователя нет в бд, добавляем.")
        add_user_to_database(user_id)

        print("Распределение админ/работник.")
        if message.from_user.id in Config.ADMINS:
            print("Вошел администратор.")
            await message.answer("Добро пожаловать, Администратор!",
                                 reply_markup=get_admin_keyboard())
            return
        else:
            print(f"Вошел работник {user_id} ")
            # Проверка на активность статуса.
            status_verification_ = status_verification(user_id)
            print(f"status_verification_ = {status_verification_}")
            if not status_verification_:
                print(f"Работник {user_id} не активный.")
                text = (
                    "Приветствую вас в боте. Если вы занимаетесь погрузо-разгрузочными работами или доставкой грузов, "
                    "здесь вы сможете получать заказы.")
                await message.answer(text,
                                     reply_markup=executor_authorization_keyboard())
                return
            print(f"Работник {user_id} активный.")
            # Проверка на заполненность личного кабинета.
            your_personal_account = checking_your_personal_account(user_id)
            if not your_personal_account:
                print(f"Личный кабинет работника {user_id} не заполнен.")
                await message.answer(
                    text="Для начала давайте познакомимся.",
                    reply_markup=acquaintance_keyboard()
                )
                return
            print(f"Личный кабинет работника {user_id} заполнен.")
            text = "Основная клавиатура"
            await message.answer(text,
                                 reply_markup=get_executor_keyboard())
            return
    except Exception as e:
        print(f"Ошибка в обработчике start: {e}")
        await message.answer("Произошла ошибка, попробуйте позже")
