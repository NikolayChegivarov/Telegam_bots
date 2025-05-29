# bot/main.py

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import os
from dotenv import load_dotenv

from bot.handlers.authorization import start, handle_authorize, handle_auth_callback
from bot.handlers.blocking import handle_block_user, handle_block_callback
from bot.handlers.history import handle_admin_panel, add_employee, handle_main_interface, handle_history
from bot.handlers.report import handle_create_report, handle_document_upload
from bot.handlers.fallback import handle_unknown

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN_BOT")


def main():
    print("🚀 Бот запускается...")

    app = Application.builder().token(TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))

    # Авторизация
    app.add_handler(MessageHandler(filters.Text("Авторизоваться"), handle_authorize))
    app.add_handler(CallbackQueryHandler(handle_auth_callback, pattern='^auth_'))

    # Административные действия
    app.add_handler(MessageHandler(filters.Text("Администрация"), handle_admin_panel))
    app.add_handler(MessageHandler(filters.Text("Добавить сотрудника"), add_employee))
    app.add_handler(MessageHandler(filters.Text("Заблокировать сотрудника"), handle_block_user))
    app.add_handler(CallbackQueryHandler(handle_block_callback, pattern='^block_'))

    # Работа с отчетами
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Создать отчет$"), handle_create_report))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))

    # История
    app.add_handler(MessageHandler(filters.Text("История запросов"), handle_history))

    # Кнопка вернуться
    app.add_handler(MessageHandler(filters.Text("Основной интерфейс"), handle_main_interface))

    # Обработка неизвестных сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    print("✅ Бот успешно запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()
