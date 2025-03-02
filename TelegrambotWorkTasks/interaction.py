# Взаимодействие.
from keyboard import Keyboards
from utils import create_bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import calendar

bot = create_bot()


@bot.message_handler(commands=['knight', 'mouse'])
def send_welcome(user_id):
    """Выяснение статуса."""
    keyboard = Keyboards().registration_keyboard()
    bot.send_message(user_id, 'Кто ты воин?', reply_markup=keyboard)


# Начальное сообщение менеджерам.
@bot.message_handler(commands=['tasks', 'set_a_task'])
def manager(user_id):
    """Начальное меню менеджеру. Просмотр задач/Поставить задачу.."""
    keyboard = Keyboards().manager_keyboard()
    text = f"_________________\n       \nВыберите действие:"
    bot.send_message(user_id, text="Выберите действие:", reply_markup=keyboard)


# Начальное сообщение водителям.
@bot.message_handler(commands=['tasks', 'my_tasks', 'status'])
def driver(user_id):
    """Начальное меню водителей. Просмотр задач/Мои задачи."""
    keyboard = Keyboards().driver_keyboard()
    bot.send_message(user_id, text="Выберите действие:", reply_markup=keyboard)


# Проверка доступа.
@bot.message_handler(commands=['accept', 'reject'])
def access_check(user_id):
    """Проверка доступа. Принять/Отклонить пользователя."""
    keyboard = Keyboards().access_check()
    text = user_id
    bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)


@bot.message_handler(commands=['kostroma', 'msk', 'filter', 'basic_menu'])
def view_filter_task(user_id):
    """Фильтр просмотра задач"""
    keyboard = Keyboards().filter_tasks_keyboard()
    text = f"_________________\n       \nВыберите нужные задачи:"
    bot.send_message(user_id, text=text, reply_markup=keyboard)


@bot.message_handler(commands=['take_task', 'to_mark'])
def alter_status_views(user_id, id_task):
    keyboard = Keyboards().alter_status()
    text = f"Выберите действие для задачи №{id_task}"
    bot.send_message(user_id, text, reply_markup=keyboard)


def create_calendar(argument):
    year = None
    month = None
    print("Создаем календарь.")
    # Если дата не указана, используем текущую
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    print("Создаем клавиатуру.")
    # Создаем клавиатуру
    markup = InlineKeyboardMarkup()

    # Добавляем кнопки навигации по месяцам
    prev_month_button = InlineKeyboardButton(
        '←',
        callback_data=f'prev-month:{year}:{month}:{argument}'
    )
    next_month_button = InlineKeyboardButton(
        '→',
        callback_data=f'next-month:{year}:{month}:{argument}'
    )

    markup.row(prev_month_button, next_month_button)

    # Получаем календарь на месяц
    cal = calendar.monthcalendar(year, month)

    # Добавляем кнопки дней
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(' ', callback_data='ignore'))
            else:
                row.append(InlineKeyboardButton(
                    str(day),
                    callback_data=f'day:{year}:{month}:{day}:{argument}'
                ))
        markup.row(*row)
    return markup
