# bot/handlers/blocking.py
from telegram import Update
from telegram.ext import ContextTypes
from database.database_interaction import DatabaseInteraction
from keyboards import get_block_keyboard

async def handle_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseInteraction()
    admin_id = update.effective_user.id

    try:
        if db.is_admin(admin_id):
            active_users = db.get_active_users()
            if active_users:
                keyboard = get_block_keyboard(active_users)
                await update.message.reply_text("Выберите пользователя для блокировки:", reply_markup=keyboard)
            else:
                await update.message.reply_text("Нет активных пользователей.")
        else:
            await update.message.reply_text("У вас нет прав для этого действия.")
    except Exception as e:
        print(f"Ошибка в handle_block_user: {e}")
    finally:
        db.close()


async def handle_block_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id

    try:
        if query.data.startswith('block_'):
            user_id = int(query.data.split('_')[1])
            db = DatabaseInteraction()

            if db.is_admin(admin_id):
                db.update_user_status(user_id, 'Заблокированный')
                await query.edit_message_text(f"Пользователь {user_id} успешно заблокирован.")
            else:
                await query.edit_message_text("У вас нет прав для этого действия.")
            db.close()
    except Exception as e:
        print(f"Ошибка в handle_block_callback: {e}")