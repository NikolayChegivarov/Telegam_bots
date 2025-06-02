# Этот модуль реализует логику диалога с пользователем для создания юридического отчета в Telegram-боте.
# Пользователь поэтапно загружает три файла: выгрузку из Контур.Фокус в формате Word (.docx),
# финансовую выгрузку в формате PDF (.pdf) и выгрузку арбитражных производств в формате Excel (.xlsx или .xls).
# Модуль проверяет статус пользователя в базе данных (доступ имеют только активные пользователи),
# обрабатывает загруженные файлы, извлекает из них структурированные данные,
# подставляет данные в шаблон Word, формирует итоговый отчет и отправляет его пользователю.
# После каждого этапа загрузки файлов пользователю возвращается подсказка по следующему шагу.
# По завершении процесса все временные файлы удаляются.
import os
from telegram import Update, InputFile, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, MessageHandler, filters, ContextTypes
from utils.extraction import extract_structured_data
from utils.recording_data import process_template
from keyboards import get_user_keyboard
from database.database_interaction import DatabaseInteraction

REPORTS_DIR = os.path.join(os.getcwd(), "Reports")
TEMPLATE_PATH = os.path.join(os.getcwd(), "шаблон.docx")

# Состояния
WAITING_WORD, WAITING_PDF, WAITING_EXCEL = range(3)

def check_active_status(user_id):
    """Проверка статуса пользователя в БД (доступ разрешен только 'Активным')."""
    db = DatabaseInteraction()
    status = db.check_user_status(user_id)
    db.close()
    return status == "Активный"

async def receive_word_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_active_status(user_id):
        await update.message.reply_text(
            "У вас нет доступа к созданию отчетов. Попросите администратора авторизовать вас.",
            reply_markup=get_user_keyboard()
        )
        return ConversationHandler.END

    document = update.message.document
    if not document or not document.file_name.endswith('.docx'):
        await update.message.reply_text("Пожалуйста, отправьте файл с расширением .docx.")
        return WAITING_WORD

    word_path = f"temp/{user_id}_Выгрузка_Контур_Фокус.docx"
    file = await document.get_file()
    await file.download_to_drive(word_path)  # <--- await обязательно!
    context.user_data['word_path'] = word_path
    await update.message.reply_text(
        "Я получил файл «Выгрузка Контур.Фокус». Прикрепите, пожалуйста, PDF-файл «Финансовая выгрузка из Контур.Фокус»."
    )
    return WAITING_PDF

async def receive_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_active_status(user_id):
        await update.message.reply_text(
            "У вас нет доступа к созданию отчетов. Попросите администратора авторизовать вас.",
            reply_markup=get_user_keyboard()
        )
        return ConversationHandler.END

    document = update.message.document
    if not document or not document.file_name.endswith('.pdf'):
        await update.message.reply_text("Пожалуйста, отправьте PDF-файл с расширением .pdf.")
        return WAITING_PDF

    pdf_path = f"temp/{user_id}_Финансовая_выгрузка_из_Контур_Фокус.pdf"
    file = await document.get_file()
    await file.download_to_drive(pdf_path)   # <--- await обязательно!
    context.user_data['pdf_path'] = pdf_path
    await update.message.reply_text(
        "Я получил файл «Финансовая выгрузка из Контур.Фокус». Прикрепите, пожалуйста, Excel-файл «Выгрузка арбитражных производств»."
    )
    return WAITING_EXCEL

async def receive_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_active_status(user_id):
        await update.message.reply_text(
            "У вас нет доступа к созданию отчетов. Попросите администратора авторизовать вас.",
            reply_markup=get_user_keyboard()
        )
        return ConversationHandler.END

    document = update.message.document
    if not document or not (document.file_name.endswith('.xlsx') or document.file_name.endswith('.xls')):
        await update.message.reply_text("Пожалуйста, отправьте Excel-файл с расширением .xlsx или .xls.")
        return WAITING_EXCEL

    excel_path = f"temp/{user_id}_Выгрузка_арбитражных_производств.xlsx"
    file = await document.get_file()
    await file.download_to_drive(excel_path)   # <--- await обязательно!
    context.user_data['excel_path'] = excel_path

    word_path = context.user_data.get('word_path')
    pdf_path = context.user_data.get('pdf_path')
    excel_path = context.user_data.get('excel_path')

    await update.message.reply_text("Обрабатываю файлы и формирую отчет. Это может занять до 1-2 минут...")

    extracted_data = extract_structured_data(word_path, pdf_path, excel_path)
    if not isinstance(extracted_data, dict) or 'error' in extracted_data:
        await update.message.reply_text(f"Ошибка при извлечении данных: {extracted_data.get('error', 'Не удалось получить данные')}")
        cleanup_files(word_path, pdf_path, excel_path)
        return ConversationHandler.END

    report_path = process_template(TEMPLATE_PATH, REPORTS_DIR, extracted_data)
    if not report_path or not os.path.exists(report_path):
        await update.message.reply_text("Ошибка при формировании шаблона. Проверьте структуру шаблона и данные.")
        cleanup_files(word_path, pdf_path, excel_path)
        return ConversationHandler.END

    await update.message.reply_document(document=InputFile(report_path), caption="Готовый отчет. Спасибо!")
    await update.message.reply_text("Выберите действие:", reply_markup=get_user_keyboard())
    cleanup_files(word_path, pdf_path, excel_path)
    return ConversationHandler.END

def cleanup_files(*filepaths):
    for f in filepaths:
        try:
            os.remove(f)
        except Exception:
            pass

def get_report_conversation_handler():
    # Entry_point — это просто кнопка "Создать отчет", не отдельная функция!
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^Создать отчет$'), receive_word_file)],
        states={
            WAITING_WORD: [MessageHandler(filters.Document.ALL, receive_word_file)],
            WAITING_PDF: [MessageHandler(filters.Document.ALL, receive_pdf_file)],
            WAITING_EXCEL: [MessageHandler(filters.Document.ALL, receive_excel_file)],
        },
        fallbacks=[],
        allow_reentry=True
    )
