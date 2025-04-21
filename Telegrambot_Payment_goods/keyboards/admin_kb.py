from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="Создать заказ")],
        [KeyboardButton(text="Посмотреть статус заказа")],
        [KeyboardButton(text="Исправить заказ")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_update_choice_keyboard():
    buttons = [
        [KeyboardButton(text="Исправить описание")],
        [KeyboardButton(text="Исправить сумму")],
        [KeyboardButton(text="Исправить описание и сумму")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
