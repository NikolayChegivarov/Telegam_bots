from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_client_main_menu():
    """Клавиатура клиента."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться на услугу")],
            [KeyboardButton(text="💇 Мои записи"), KeyboardButton(text="💼 Мой профиль")],
            [KeyboardButton(text="📋 Услуги и цены")]
        ],
        resize_keyboard=True
    )


def edit_profile_menu():
    """Меню профиля."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="✏️ Редактировать имя")],
            [KeyboardButton(text="📱 Изменить телефон"), KeyboardButton(text="✏️ Редактировать фамилию")]
        ],
        resize_keyboard=True
    )


def get_master_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Мои записи")],
            [KeyboardButton(text="💼 Мой профиль"), KeyboardButton(text="📋 Мои услуги")],
            [KeyboardButton(text="📊 График работы")]
        ],
        resize_keyboard=True
    )


def get_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


def get_services_kb(services):
    kb = InlineKeyboardMarkup()
    for service in services:
        kb.add(InlineKeyboardButton(
            text=f"{service[1]} - {service[2]} руб. ({service[3]} мин)",
            callback_data=f"service_{service[0]}"
        ))
    return kb


def get_confirm_appointment_kb(appointment_id):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{appointment_id}"),
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{appointment_id}")
    )


def get_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍💼 Добавить мастера")],
            [KeyboardButton(text="➕ Добавить услугу")],
            [KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True
    )
