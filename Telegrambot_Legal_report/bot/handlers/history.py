from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from history.history_manager import get_history_by_days

# Состояние для FSM
AWAIT_DAYS = 1

# Старт истории
async def start_history_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("За сколько дней вы хотите получить историю?")
    return AWAIT_DAYS

# Обработка введённого числа
async def process_days_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text)
        if days > 999:
            await update.message.reply_text("Максимальное количество запроса истории 999 дней")
            return ConversationHandler.END

        history = get_history_by_days(days)

        if not history:
            await update.message.reply_text("Нет записей за этот период.")
        else:
            text = "\n".join(
                [f"{entry['timestamp']} — {entry['org']} ({entry['filename']})" for entry in history]
            )
            await update.message.reply_text(f"🗂 История за {days} дней:\n\n{text}")
    except ValueError:
        await update.message.reply_text("Введите число — количество дней.")
    return ConversationHandler.END

# Отмена (если надо)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запрос истории отменён.")
    return ConversationHandler.END
