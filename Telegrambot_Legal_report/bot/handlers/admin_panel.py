# bot/handlers/admin_panel.py

from telegram import Update
from telegram.ext import ContextTypes
from database.database_interaction import DatabaseInteraction
from keyboards import get_admin_keyboard, get_user_keyboard, administrative_keyboard, get_auth_keyboard


# 🛠 "Администрация"
async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вызывает панель администрирования."""
    db = DatabaseInteraction()
    user_id = update.effective_user.id

    try:
        if db.is_admin(user_id):
            await update.message.reply_text("Панель администратора", reply_markup=administrative_keyboard())
        else:
            await update.message.reply_text("У вас нет прав доступа")
    except Exception as e:
        print(f"Ошибка в handle_admin_panel: {e}")
    finally:
        db.close()


async def add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предоставляет пользователей для блокировки."""
    db = DatabaseInteraction()
    admin_id = update.effective_user.id

    try:
        if db.is_admin(admin_id):
            blocked_users = db.get_blocked_users()
            if blocked_users:
                keyboard = get_auth_keyboard(blocked_users)
                await update.message.reply_text("Выберите пользователя для авторизации:", reply_markup=keyboard)
            else:
                await update.message.reply_text("Нет пользователей, ожидающих авторизации.")
        else:
            await update.message.reply_text("У вас нет прав для этого действия.")
    finally:
        db.close()


async def handle_main_interface(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдает основную клавиатуру после проверки на активность и на права администратора."""
    db = DatabaseInteraction()
    user_id = update.effective_user.id

    # поддержка как text, так и callback
    message = update.message or (update.callback_query and update.callback_query.message)

    try:
        if db.is_admin(user_id):
            await message.reply_text(
                "Вы вернулись в основной интерфейс администратора.",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.reply_text(
                "Вы вернулись в основной интерфейс сотрудника.",
                reply_markup=get_user_keyboard()
            )
    except Exception as e:
        print(f"Ошибка в handle_main_interface: {e}")
    finally:
        db.close()

