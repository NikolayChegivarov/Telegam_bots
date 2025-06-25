# Отчеты
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import reports, get_history_period_keyboard
from database.history_manager import read_history
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from database.history_manager import read_history
import os
from telegram.ext import CallbackQueryHandler
import traceback


async def reports_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реагирует на кнопку 'Отчеты'. Отправляет пользователю клавиатуру для получения отчетов."""
    keyboard = reports()
    await update.message.reply_text("Выберите действие:", reply_markup=reports())


async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предлагает выбрать количество месяцев для отображения истории отчетов."""
    await update.message.reply_text(
        "За сколько месяцев показать историю отчетов?",
        reply_markup=get_history_period_keyboard()
    )


async def handle_history_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mapping = {
        "1 месяц": 1,
        "2 месяца": 2,
        "3 месяца": 3
    }

    if text not in mapping:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return

    period_index = mapping[text]

    try:
        history = read_history(period_index)  # [(org_name, file_path, created_at), ...]

        if not history:
            await update.message.reply_text("Отчеты за выбранный период отсутствуют.")
            return

        # Сохраняем историю во временные данные пользователя
        context.user_data['history_files'] = history

        keyboard = []
        for idx, (org_name, file_path, created_at) in enumerate(history):
            filename = os.path.basename(file_path)
            button = InlineKeyboardButton(
                text=filename,
                callback_data=f"GET_REPORT_{idx}"  # короткий callback
            )
            keyboard.append([button])  # одна кнопка в строке

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Выберите нужный отчет:",
            reply_markup=reply_markup
        )

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка при получении истории: {e}")


async def handle_report_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("GET_REPORT_"):
        return

    idx = int(data.replace("GET_REPORT_", ""))
    history = context.user_data.get("history_files", [])

    if idx >= len(history):
        await query.edit_message_text("❌ Отчет не найден.")
        return

    _, file_path, _ = history[idx]

    if not os.path.exists(file_path):
        await query.edit_message_text("❌ Файл не найден.")
        return

    try:
        with open(file_path, "rb") as f:
            await query.message.reply_document(
                InputFile(f, filename=os.path.basename(file_path))
            )
    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
        await query.edit_message_text("❌ Не удалось отправить файл.")


async def make_a_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реагирует на 'Извлечь отчет'
    """


