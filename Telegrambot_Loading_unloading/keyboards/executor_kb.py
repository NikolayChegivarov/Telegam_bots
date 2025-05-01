from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def executor_authorization_keyboard():
    print("Клавиатура хочу работать")
    buttons = [
        [KeyboardButton(text="Хочу работать! 👷")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def acquaintance_keyboard():
    buttons = [
        [KeyboardButton(text="Начать знакомство 🤝")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
    ],
    resize_keyboard=True
)

def get_executor_keyboard():
    buttons = [
        [KeyboardButton(text="Список активных задач 📋")],
        [KeyboardButton(text="Взять задачу ➡️")],
        [KeyboardButton(text="Заявка выполнена ✅")],
        [KeyboardButton(text="Отказаться от задачи ❌")],
        [KeyboardButton(text="Личный кабинет 👨‍💻")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def personal_office_keyboard():
    buttons = [
        [KeyboardButton(text="Мои задачи 📖")],
        [KeyboardButton(text="Мои данные 📑")],
        [KeyboardButton(text="Статистика заявок 📊")],
        [KeyboardButton(text="Поддержка 🤖")],
        [KeyboardButton(text="Основное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def update_data():
    buttons = [
        [KeyboardButton(text="Обновить данные 🤝")],
        [KeyboardButton(text="Основное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def support():
    buttons = [
        [KeyboardButton(text="Как работать с заказами:")],
        [KeyboardButton(text="Важные правила")],
        [KeyboardButton(text="Основное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
