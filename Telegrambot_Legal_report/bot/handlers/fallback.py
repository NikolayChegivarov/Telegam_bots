# bot/handlers/fallback.py
from telegram import Update
from telegram.ext import ContextTypes

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда не распознана. Пожалуйста, используйте кнопки.")

