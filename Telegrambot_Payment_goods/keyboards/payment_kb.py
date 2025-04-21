from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_payment_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Оплатить услугу", callback_data="pay_service"),
                InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")
            ]
        ]
    )
