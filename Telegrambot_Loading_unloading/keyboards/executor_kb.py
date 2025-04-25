from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_executor_authorization():
    buttons = [
        [KeyboardButton(text="Хочу работать! 🤝")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_executor_keyboard():
    buttons = [
        [KeyboardButton(text="Список активных задач 📋")],
        [KeyboardButton(text="Взять задачу ➡️")],
        [KeyboardButton(text="Личный кабинет 👨‍💻")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def create_task_response_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для отклика на задачу"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Откликнуться на задачу",
                callback_data=f"respond_task_{task_id}"
            )
        ]
    ])
    return keyboard
