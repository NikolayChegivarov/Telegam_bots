# main.py
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from dotenv import load_dotenv
import os

from bot.handlers.authorization import handle_authorize, start, handle_auth_callback, handle_main_interface, handle_admin_panel, add_employee
from bot.handlers.blocking import handle_block_user, handle_block_callback
from bot.handlers.fallback import handle_unknown
from bot.handlers.history import start_history_request, process_days_input, cancel  # Новый импорт

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN_BOT")

# Состояния для ConversationHandler истории
AWAIT_DAYS = 1

def main():
    print("БОТ ЗАПУСКАЕТСЯ...")
    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))

    # Обработчик истории запросов (через /history)
    history_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("history", start_history_request)],
        states={
            AWAIT_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_days_input)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(history_conv_handler)

    # Кнопки
    application.add_handler(MessageHandler(filters.Text("Авторизоваться"), handle_authorize))
    application.add_handler(MessageHandler(filters.Text("Администрация"), handle_admin_panel))
    application.add_handler(MessageHandler(filters.Text("Добавить сотрудника"), add_employee))
    application.add_handler(MessageHandler(filters.Text("Заблокировать сотрудника"), handle_block_user))
    application.add_handler(MessageHandler(filters.Text("Основной интерфейс"), handle_main_interface))

    # Callback-инлайн-кнопки для активации и блокировки сотрудников
    application.add_handler(CallbackQueryHandler(handle_auth_callback, pattern='^auth_'))
    application.add_handler(CallbackQueryHandler(handle_block_callback, pattern='^block_'))

    # Остальные сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    print("БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ")
    application.run_polling()

if __name__ == "__main__":
    main()
