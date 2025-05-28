from dotenv import load_dotenv
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from database_interaction import DatabaseInteraction
from keyboards import (
    get_admin_keyboard,
    get_user_keyboard,
    get_blocked_keyboard,
    get_auth_keyboard,
    administrative_keyboard
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN_BOT")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseInteraction()
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name
    last_name = user.last_name or ""

    print(f"Пользователь {user_id} начал взаимодействие с ботом")

    try:
        if db.is_admin(user_id):
            await update.message.reply_text("Добро пожаловать, администратор", reply_markup=get_admin_keyboard())
        else:
            status = db.check_user_status(user_id)
            if status == "Активный":
                await update.message.reply_text("Начнем работу!", reply_markup=get_user_keyboard())
            else:
                await update.message.reply_text(
                    "Привет. Я бот для заполнения шаблона юридической информацией. "
                    "Для авторизации нажмите АВТОРИЗОВАТЬСЯ, если зашли по ошибке — просто покиньте этот бот.",
                    reply_markup=get_blocked_keyboard()
                )
    except Exception as e:
        print(f"Ошибка в start: {e}")
    finally:
        db.close()


async def handle_authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Авторизация"""
    db = DatabaseInteraction()
    user = update.effective_user
    user_id = user.id

    try:
        print(f"Пользователь {user_id} нажал 'Авторизоваться'")
        if not db.check_user_status(user_id):
            db.add_user(user_id, user.first_name, user.last_name or "")
            await update.message.reply_text("Ваш запрос находится на согласовании у администратора бота")
        else:
            await update.message.reply_text("Ваш запрос уже находится на рассмотрении")
    except Exception as e:
        print(f"Ошибка в handle_authorize: {e}")
    finally:
        db.close()


async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присылает клавиатуру администрирования."""
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
    """Присылает клавиатуру для добавления сотрудника."""
    db = DatabaseInteraction()
    admin_id = update.effective_user.id

    try:
        print(f"Администратор {admin_id} запросил добавление сотрудника")
        if db.is_admin(admin_id):
            blocked_users = db.get_blocked_users()
            if blocked_users:
                keyboard = get_auth_keyboard(blocked_users)
                await update.message.reply_text("Выберите пользователя для авторизации:", reply_markup=keyboard)
            else:
                await update.message.reply_text("Нет пользователей, ожидающих авторизации.")
        else:
            await update.message.reply_text("У вас нет прав для этого действия.")
    except Exception as e:
        print(f"Ошибка в add_employee: {e}")
    finally:
        db.close()


async def handle_auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активизирует выбранного пользователя."""
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id

    try:
        if query.data.startswith('auth_'):
            user_id = int(query.data.split('_')[1])
            db = DatabaseInteraction()

            if db.is_admin(admin_id):
                db.update_user_status(user_id, 'Активный')
                await query.edit_message_text(f"Пользователь {user_id} успешно авторизован!")
            else:
                await query.edit_message_text("У вас нет прав для этого действия.")

            db.close()
    except Exception as e:
        print(f"Ошибка в handle_auth_callback: {e}")


async def handle_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присылает клавиатуру для блокировки пользователей."""
    db = DatabaseInteraction()
    admin_id = update.effective_user.id

    try:
        if db.is_admin(admin_id):
            active_users = db.get_active_users()
            if active_users:
                from keyboards import get_block_keyboard
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
    """Блокирует выбранного пользователя."""
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



async def handle_main_interface(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseInteraction()
    user_id = update.effective_user.id

    try:
        if db.is_admin(user_id):
            await update.message.reply_text(
                "Вы вернулись в основной интерфейс администратора.",
                reply_markup=get_admin_keyboard()
            )
        else:
            await update.message.reply_text("У вас нет прав доступа.")
    except Exception as e:
        print(f"Ошибка в handle_main_interface: {e}")
    finally:
        db.close()


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда не распознана. Пожалуйста, используйте кнопки.")


def main():
    try:
        print("БОТ ЗАПУСКАЕТСЯ...")
        application = Application.builder().token(TOKEN).build()

        # Команды
        application.add_handler(CommandHandler("start", start))

        # Кнопки
        application.add_handler(MessageHandler(filters.Text("Авторизоваться"), handle_authorize))
        application.add_handler(MessageHandler(filters.Text("Администрация"), handle_admin_panel))
        application.add_handler(MessageHandler(filters.Text("Добавить сотрудника"), add_employee))
        application.add_handler(MessageHandler(filters.Text("Заблокировать сотрудника"), handle_block_user))
        application.add_handler(MessageHandler(filters.Text("Основной интерфейс"), handle_main_interface))

        # Callback-инлайн-кнопки для активации и блокировки сотрудников.
        application.add_handler(CallbackQueryHandler(handle_auth_callback, pattern='^auth_'))
        application.add_handler(CallbackQueryHandler(handle_block_callback, pattern='^block_'))

        # Остальные сообщения
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))


        print("БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ")
        application.run_polling()

    except KeyboardInterrupt:
        print("\nБОТ ОСТАНОВЛЕН ПОЛЬЗОВАТЕЛЕМ")
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
    finally:
        print("БОТ ЗАВЕРШИЛ РАБОТУ")


if __name__ == "__main__":
    main()
