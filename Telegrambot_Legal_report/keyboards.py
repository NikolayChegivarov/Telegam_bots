from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_keyboard():
    """Основная клавиатура администратора."""
    keyboard = [
        [KeyboardButton("Создать отчет"), KeyboardButton("Администрация")],
        [KeyboardButton("История запросов"), KeyboardButton("Извлечь отчет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_keyboard():
    """Основная клавиатура сотрудника."""
    keyboard = [
        [KeyboardButton("Создать отчет")],
        [KeyboardButton("История запросов"), KeyboardButton("Извлечь отчет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_blocked_keyboard():
    """Запрос авторизации."""
    keyboard = [
        [KeyboardButton("Авторизоваться")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def administrative_keyboard():
    """Админ панель."""
    keyboard = [
        [KeyboardButton("Добавить сотрудника")],
        [KeyboardButton("Заблокировать сотрудника")],
        [KeyboardButton("Основной интерфейс")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_auth_keyboard(users):
    """Создает инлайн-клавиатуру для авторизации пользователей."""
    keyboard = []
    for user_id, first_name, last_name in users:
        name = f"{first_name} {last_name}" if last_name else first_name
        button = InlineKeyboardButton(
            f"Авторизовать {name}",
            callback_data=f"auth_{user_id}"
        )
        keyboard.append([button])
    return InlineKeyboardMarkup(keyboard)

def get_block_keyboard(users):
    """Создает инлайн-клавиатуру для блокировки пользователей."""
    keyboard = []
    for user_id, first_name, last_name in users:
        name = f"{first_name} {last_name}" if last_name else first_name
        button = InlineKeyboardButton(
            f"Заблокировать {name}",
            callback_data=f"block_{user_id}"
        )
        keyboard.append([button])
    return InlineKeyboardMarkup(keyboard)
