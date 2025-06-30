# bot/main.py

import os
from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from telegram.error import NetworkError

from bot.handlers.authorization import start, handle_authorize, handle_auth_callback
from bot.handlers.blocking_user import handle_block_user, handle_block_callback
from bot.handlers.admin_panel import handle_admin_panel, add_employee, handle_main_interface
from bot.handlers.fallback import handle_unknown
from bot.handlers.create_report import get_report_conversation_handler
from bot.handlers.view_reports import (
    reports_panel,
    handle_history,
    handle_history_period,
    handle_extract_report,
    handle_org_name_input,
    handle_send_report_by_search,
    handle_report_file_callback,
    handle_main_interface_callback,
    handle_history_file,
    ASK_ORG_NAME
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN_BOT")

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
app.add_handler(CallbackQueryHandler(handle_auth_callback, pattern='^approve_'))
app.add_handler(MessageHandler(filters.Text("Заблокировать сотрудника"), handle_block_user))
app.add_handler(CallbackQueryHandler(handle_block_callback, pattern='^block_'))
app.add_handler(MessageHandler(filters.Text("Основной интерфейс"), handle_main_interface))

# Работа с отчетами
app.add_handler(get_report_conversation_handler())
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Отчеты$"), reports_panel))
app.add_handler(MessageHandler(filters.Text("История запросов"), handle_history))
app.add_handler(MessageHandler(filters.Text(["1 месяц", "2 месяца", "3 месяца"]), handle_history_period))
app.add_handler(CallbackQueryHandler(handle_report_file_callback, pattern="^GET_REPORT_"))
app.add_handler(CallbackQueryHandler(handle_main_interface_callback, pattern="^TO_MAIN_INTERFACE$"))
app.add_handler(ConversationHandler(
    entry_points=[MessageHandler(filters.Text("Извлечь отчет"), handle_extract_report)],
    states={ASK_ORG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_org_name_input)]},
    fallbacks=[]
))
app.add_handler(CallbackQueryHandler(handle_send_report_by_search, pattern="^SEND_REPORT_"))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Файл истории$"), handle_history_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

print("✅ Бот успешно запущен.\n")

# Просто запуск, без asyncio.run и без циклов
app.run_polling()
