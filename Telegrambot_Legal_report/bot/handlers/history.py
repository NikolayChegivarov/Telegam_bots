# bot/handlers/history.py

from telegram import Update
from telegram.ext import ContextTypes
from database.database_interaction import DatabaseInteraction
from keyboards import get_admin_keyboard, administrative_keyboard, get_auth_keyboard
from history.history_manager import read_history


async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseInteraction()
    user_id = update.effective_user.id

    try:
        if db.is_admin(user_id):
            await update.message.reply_text("Панель администратора", reply_markup=administrative_keyboard())
        else:
            await update.message.reply_text("У вас нет прав доступа.")
    finally:
        db.close()


async def add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    db = DatabaseInteraction()
    user_id = update.effective_user.id

    try:
        if db.is_admin(user_id):
            await update.message.reply_text("Вы вернулись в основной интерфейс администратора.",
                                            reply_markup=get_admin_keyboard())
        else:
            await update.message.reply_text("У вас нет прав доступа.")
    finally:
        db.close()


async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = read_history()
    if history:
        response = "История сформированных отчетов:\n\n" + ", ".join(history)
    else:
        response = "История пуста."
    await update.message.reply_text(response)
