# bot/handlers/report.py
# Поведение команды «Создать отчет»:
# Отправляется просьба прикрепить Word-файл.
# После получения — запрос PDF.
# Затем — Excel.
# После получения всех файлов: вывод сообщения о начале обработки.
# bot/handlers/report.py
from telegram import Update, Document
from telegram.ext import ContextTypes
import os
from bot.state_machine import ReportState
from utils.extraction import extract_from_word, extract_from_pdf, extract_from_excel
from utils.recording_data import process_template

user_states = {}
user_data = {}

async def handle_create_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = ReportState.AWAITING_WORD
    user_data[user_id] = {}
    await update.message.reply_text("Прикрепите, пожалуйста, Word-файл «Выгрузка Контур.Фокус».")

async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    document: Document = update.message.document

    if not document:
        await update.message.reply_text("❌ Пожалуйста, прикрепите файл.")
        return

    file = await document.get_file()
    file_name = document.file_name
    file_path = f"temp/{user_id}_{file_name}"
    os.makedirs("temp", exist_ok=True)
    await file.download_to_drive(file_path)

    state = user_states.get(user_id)

    if state == ReportState.AWAITING_WORD:
        user_data[user_id]['word'] = file_path
        user_states[user_id] = ReportState.AWAITING_PDF
        await update.message.reply_text("Я получил файл «Выгрузка Контур.Фокус». Прикрепите, пожалуйста, PDF-файл «Финансовая выгрузка из Контур.Фокус».")

    elif state == ReportState.AWAITING_PDF:
        user_data[user_id]['pdf'] = file_path
        user_states[user_id] = ReportState.AWAITING_EXCEL
        await update.message.reply_text("Я получил файл «Финансовая выгрузка из Контур.Фокус».\n\nПрикрепите, пожалуйста, Excel-файл «Выгрузка арбитражных производств».")

    elif state == ReportState.AWAITING_EXCEL:
        user_data[user_id]['excel'] = file_path
        user_states[user_id] = ReportState.COMPLETE
        await update.message.reply_text("📥 Все файлы получены. Начинаю обработку...")

        try:
            # Извлечение данных
            word_data = extract_from_word(user_data[user_id]['word'])
            pdf_data = extract_from_pdf(user_data[user_id]['pdf'])
            excel_data = extract_from_excel(user_data[user_id]['excel'])

            # Объединение всех данных в один словарь
            combined_data = {**word_data, **pdf_data, **excel_data}

            # Путь к шаблону
            template_path = "шаблон.docx"

            # Генерация и сохранение файла
            success = process_template(template_path, None, combined_data)

            if success:
                await update.message.reply_text("✅ Отчет успешно сформирован и сохранен в папку Reports.")
            else:
                await update.message.reply_text("❌ Ошибка при формировании отчета.")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при обработке: {e}")

        # Очистка временных данных
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)

    else:
        await update.message.reply_text("⚠️ Неожиданное состояние. Попробуйте заново командой «Создать отчет».")
