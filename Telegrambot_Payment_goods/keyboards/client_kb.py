from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_client_keyboard():
    buttons = [
        [KeyboardButton(text="Выбрать услугу для оплаты")],
        [KeyboardButton(text="Посмотреть статус услуги")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
