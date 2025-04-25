from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_executor_keyboard():
    buttons = [
        [KeyboardButton(text="Список активных задач 📝")],
        [KeyboardButton(text="Взять задачу 🔔")],
        [KeyboardButton(text="Личный кабинет ")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
