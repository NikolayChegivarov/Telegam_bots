from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать", callback_data="start")]
        ]
    )


def danger_testing():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Есть опасность", callback_data="danger")],
            [InlineKeyboardButton(text="Нет опасности", callback_data="no_danger")],
        ]
    )


def security():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Нет опасности", callback_data="no_danger")],
            [InlineKeyboardButton(text="Предыдущий этап", callback_data="start")]
        ]
    )


def consciousness_testing():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="В сознании", callback_data="in_consciousness")],
            [InlineKeyboardButton(text="Без сознания", callback_data="no_consciousness")],
            [InlineKeyboardButton(text="Предыдущий этап", callback_data="start")]
        ]
    )


def bleeding_testing():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Есть кровотечение", callback_data="is_bleeding")],
            [InlineKeyboardButton(text="Нет кровотечения", callback_data="no_bleeding")],
            [InlineKeyboardButton(text="Предыдущий этап", callback_data="no_danger")]
        ]
    )


def intensive_testing():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Интенсивное", callback_data="intensive")],
            [InlineKeyboardButton(text="Не интенсивное", callback_data="no_intensive")],
            [InlineKeyboardButton(text="Предыдущий этап", callback_data="no_danger")]
        ]
    )


def blood_stop():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получается", callback_data="it_worked")],
            [InlineKeyboardButton(text="Не получается", callback_data="no_worked")],
            [InlineKeyboardButton(text="Предыдущий этап", callback_data="no_danger")]
        ]
    )


def it_worked():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="intensive")],
            [InlineKeyboardButton(text="Нет", callback_data="no_intensive")],
            [InlineKeyboardButton(text="Рассказать как делается давящая повязка?", callback_data="no_danger")]
        ]
    )
