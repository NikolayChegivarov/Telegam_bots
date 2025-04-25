from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="Поставить задачу 📝")],
        [KeyboardButton(text="Просмотр всех задач")],
        [KeyboardButton(text="Исполнители")],
        [KeyboardButton(text="Удалить задачу")],
        [KeyboardButton(text="Закрыть задачу")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


