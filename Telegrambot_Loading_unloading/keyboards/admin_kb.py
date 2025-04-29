from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="Поставить задачу 📝")],
        [KeyboardButton(text="Список активных задач 📋")],
        [KeyboardButton(text="Завершить задачу 📁")],
        [KeyboardButton(text="Удалить задачу ❌")],
        [KeyboardButton(text="Исполнители 👥")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def authorization_keyboard(user_id: int):
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить работника",
                                callback_data=f"add_worker_{user_id}"),
            InlineKeyboardButton(text="Главное меню",
                                callback_data=f"ignore_{user_id}")]
    ])
    return admin_keyboard
