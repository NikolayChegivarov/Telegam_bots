from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="Меню задач 📝")],
        [KeyboardButton(text="Исполнители 👥")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def tasks_keyboard():
    buttons = [
        [KeyboardButton(text="Поставить задачу 📝")],
        [KeyboardButton(text="Активные задачи 📋")],
        [KeyboardButton(text="Завершить задачу 📁")],
        [KeyboardButton(text="Удалить задачу ❌")],
        [KeyboardButton(text="Главное меню 🔙")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def performers_keyboard():
    buttons = [
        [KeyboardButton(text="Посмотреть анкету исполнителя 🗄")],
        [KeyboardButton(text="Статистика исполнителя 📊")],
        [KeyboardButton(text="Заблокировать исполнителя 👊")],
        [KeyboardButton(text="Главное меню 🔙")],
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





