from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_client_keyboard():
    buttons = [
        [KeyboardButton(text="Оплатить услугу")],
        [KeyboardButton(text="Посмотреть статус услуги")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_payment_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Оплатить услугу", callback_data="pay_service")],
        [InlineKeyboardButton(text="Вернуться к выбору услуги", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)