import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import os
import traceback

from bot.handlers.admin_panel import handle_main_interface
from database.history_manager import read_history, get_all_history
from database.database_interaction import DatabaseInteraction
from keyboards import reports
REPORTS_DIR = os.path.join(os.getcwd(), "Reports")

ASK_ORG_NAME = range(1)


async def reports_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реагирует на кнопку 'Отчеты'. Отправляет пользователю клавиатуру для получения отчетов."""
    keyboard = reports()
    await update.message.reply_text("Выберите действие:", reply_markup=keyboard)


# "История запросов"
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

        # Удаляем клавиатуру выбора месяцев (без вывода сообщения)
        await update.message.reply_text(
            text=".",  # невидимый символ
            reply_markup=ReplyKeyboardRemove()
        )

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(f"❌ Ошибка при получении истории: {e}")


async def handle_report_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит выбранный инлайн кнопкой отчет."""
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
    """Подтверждает получение callback.
    Перенаправляет вызов на основную функцию обработки главного интерфейса"""
    query = update.callback_query
    await query.answer()
    await handle_main_interface(update, context)


# "Извлечь отчет"
async def handle_extract_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название организации или часть названия:")
    return ASK_ORG_NAME


async def handle_org_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower()
    matching_files = []

    for file in os.listdir(REPORTS_DIR):
        if file.lower().endswith(".docx") and query in file.lower():
            matching_files.append(file)

    if not matching_files:
        await update.message.reply_text("По вашему запросу ничего не найдено.")
        return ConversationHandler.END

    context.user_data["search_files"] = matching_files

    keyboard = [
        [InlineKeyboardButton(text=filename, callback_data=f"SEND_REPORT_{idx}")]
        for idx, filename in enumerate(matching_files)
    ]

    # Добавляем кнопку "🏠 Основной интерфейс"
    keyboard.append([
        InlineKeyboardButton(text="🏠 Основной интерфейс", callback_data="TO_MAIN_INTERFACE")
    ])

    await update.message.reply_text(
        "Выберите нужный отчет или вернитесь в основной интерфейс:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# Обработка выбранного отчета по индексу
async def handle_send_report_by_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        idx_str = query.data.replace("SEND_REPORT_", "")
        idx = int(idx_str)
        matching_files = context.user_data.get("search_files", [])

        if idx < 0 or idx >= len(matching_files):
            await query.edit_message_text("❌ Неверный выбор отчета.")
            return

        filename = matching_files[idx]
        filepath = os.path.join(REPORTS_DIR, filename)

        if not os.path.exists(filepath):
            await query.edit_message_text("❌ Файл не найден.")
            return

        with open(filepath, "rb") as f:
            await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(f))

    except Exception as e:
        traceback.print_exc()
        await query.edit_message_text(f"❌ Ошибка при отправке отчета: {e}")

# "Файл истории"
TEMP_HISTORY_FILE = "temp/history_file.xlsx"

async def handle_history_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    try:
        await update.message.reply_text("Готовлю файл с историей...")

        history_data = get_all_history()
        if not history_data:
            await context.bot.send_message(chat_id=chat_id, text="История пуста.")
            return

        df = pd.DataFrame(history_data)
        df.to_excel(TEMP_HISTORY_FILE, index=False)

        with open(TEMP_HISTORY_FILE, "rb") as f:
            await context.bot.send_document(chat_id=chat_id, document=InputFile(f))

    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(f"❌ Произошла сетевая ошибка: {e}")

    finally:
        if os.path.exists(TEMP_HISTORY_FILE):
            os.remove(TEMP_HISTORY_FILE)