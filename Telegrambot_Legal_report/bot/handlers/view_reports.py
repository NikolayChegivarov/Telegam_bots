from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, ReplyKeyboardRemove, \
    ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import os
import traceback

from bot.handlers.admin_panel import handle_main_interface
from database.history_manager import read_history
# from database.database_interaction import DatabaseInteraction
from keyboards import reports


async def reports_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реагирует на кнопку 'Отчеты'. Отправляет пользователю клавиатуру для получения отчетов."""
    keyboard = reports()
    await update.message.reply_text("Выберите действие:", reply_markup=keyboard)


async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выберите период, за который вы хотите просмотреть отчеты:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ["1 месяц", "2 месяца", "3 месяца"]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
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
        history = read_history(period_index)
        if not history:
            await update.message.reply_text("Отчеты за выбранный период отсутствуют.")
            return

        context.user_data['history_files'] = history

        # Формируем кнопки
        keyboard = []
        for idx, (org_name, file_path, created_at) in enumerate(history):
            filename = os.path.basename(file_path)
            keyboard.append([
                InlineKeyboardButton(text=filename, callback_data=f"GET_REPORT_{idx}")
            ])

        # Добавляем кнопку "Основной интерфейс"
        keyboard.append([
            InlineKeyboardButton(text="🏠 Основной интерфейс", callback_data="TO_MAIN_INTERFACE")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем инлайн-кнопки
        await update.message.reply_text(
            "Выберите нужный отчет или вернитесь в основной интерфейс:",
            reply_markup=reply_markup
        )

        # Удаляем клавиатуру выбора месяцев
        await update.message.reply_text(
            "⏳ Скрываю временные кнопки периода...",
            reply_markup=ReplyKeyboardRemove()
        )

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка при получении истории: {e}")


async def handle_report_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        data = query.data
        if not data.startswith("GET_REPORT_"):
            return

        idx = int(data.replace("GET_REPORT_", ""))
        history_files = context.user_data.get('history_files', [])
        if idx >= len(history_files):
            await query.edit_message_text("❌ Неверный выбор файла.")
            return

        _, file_path, _ = history_files[idx]
        if not os.path.exists(file_path):
            await query.edit_message_text("❌ Файл не найден на сервере.")
            return

        with open(file_path, "rb") as f:
            await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(f))

    except Exception as e:
        traceback.print_exc()
        await query.edit_message_text(f"❌ Ошибка при отправке файла: {e}")


async def handle_main_interface_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия инлайн-кнопки возврата в основной интерфейс."""
    query = update.callback_query
    await query.answer()

    # Вызываем уже готовую функцию — она сама всё сделает
    await handle_main_interface(update, context)
