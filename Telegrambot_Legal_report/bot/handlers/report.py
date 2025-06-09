import os
from telegram import Update, InputFile, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler,
    MessageHandler, CommandHandler, filters
)

from keyboards import get_user_keyboard
from utils.extraction import extract_structured_data
from utils.recording_data import save_filled_doc, generate_filename
from database.database_interaction import DatabaseInteraction
from database.history_manager import write_to_history
from pprint import pprint

REPORTS_DIR = os.path.join(os.getcwd(), "Reports")
TEMPLATE_PATH = os.path.join(os.getcwd(), "шаблон.docx")
TEMP_DIR = os.path.join(os.getcwd(), "temp")

WAITING_WORD, WAITING_FIN, WAITING_EXCEL = range(3)

user_files = {}


def pretty_print_data(data: dict):
    print("\nПолучили данные с 3х файлов:")
    pprint(data)
    print("\n")


def print_separator():
    print("=" * 60)


async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"Пользователь {user_id} формирует отчет:")
    print("Начинаем сбор данных")

    db = DatabaseInteraction()

    try:
        status = db.check_user_status(user_id)

        if status == "Активный":
            print(f"Запросили у пользователя {user_id} документ .docx")
            await update.message.reply_text(
                "Прикрепите, пожалуйста, Word-файл «Выгрузка Контур.Фокус»."
            )
            return WAITING_WORD

        elif status == "Заблокированный":
            await update.message.reply_text(
                "❌ Вам ограничили доступ к сервису.",
                reply_markup=get_user_keyboard()
            )
        else:
            await update.message.reply_text(
                "⚠️ У вас нет доступа к созданию отчетов. Попросите администратора авторизовать вас.",
                reply_markup=get_user_keyboard()
            )

    except Exception as e:
        print(f"Ошибка в start_report: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

    finally:
        db.close()

    return ConversationHandler.END


async def receive_word_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    user_id = update.effective_user.id

    if not document or not document.file_name.endswith('.docx'):
        await update.message.reply_text("❌ Пожалуйста, прикрепите Word-файл .docx")
        return WAITING_WORD

    word_path = os.path.join(TEMP_DIR, f"{user_id}_word.docx")
    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(word_path)
    user_files[user_id] = {'word': word_path}

    print(f"Получили от пользователя {user_id} документ .docx")
    print(f"Запросили у пользователя {user_id} документ .pdf")
    await update.message.reply_text("Я получил файл «Выгрузка Контур.Фокус». Прикрепите, пожалуйста, PDF-файл «Финансовая выгрузка из Контур.Фокус».")
    return WAITING_FIN


async def receive_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    user_id = update.effective_user.id

    if not document or not document.file_name.endswith('.pdf'):
        await update.message.reply_text("❌ Пожалуйста, прикрепите PDF-файл .pdf")
        return WAITING_FIN

    pdf_path = os.path.join(TEMP_DIR, f"{user_id}_fin.pdf")
    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(pdf_path)
    user_files[user_id]['pdf'] = pdf_path

    print(f"Получили от пользователя {user_id} документ .pdf")
    print(f"Запросили у пользователя {user_id} документ .xlsx")
    await update.message.reply_text("Я получил файл «Финансовая выгрузка из Контур.Фокус». Прикрепите, пожалуйста, Excel-файл «Выгрузка арбитражных производств».")
    return WAITING_EXCEL


async def receive_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    user_id = update.effective_user.id

    if not document or not document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("❌ Пожалуйста, прикрепите Excel-файл .xlsx или .xls")
        return WAITING_EXCEL

    excel_path = os.path.join(TEMP_DIR, f"{user_id}_arb.xlsx")
    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(excel_path)
    user_files[user_id]['excel'] = excel_path

    print(f"Получили от пользователя {user_id} документ .xlsx")
    print("Собрали все три файла.")

    try:
        combined_data = extract_structured_data(
            user_files[user_id]['word'],
            user_files[user_id]['pdf'],
            user_files[user_id]['excel']
        )

        combined_data['org_name'] = combined_data.get('Краткое наименование', 'Без названия')
        pretty_print_data(combined_data)

        print("Заносим информацию в шаблон")
        output_path = os.path.join(REPORTS_DIR, generate_filename(combined_data))


        save_filled_doc(TEMPLATE_PATH, output_path, combined_data)
        print(f"Сохранили новый файл {os.path.basename(output_path)} в папку Reports")

        await update.message.reply_document(
            InputFile(
                output_path,
                filename=os.path.basename(output_path)
            )
        )

        await update.message.reply_text("✅ Отчет успешно сформирован и отправлен вам.")

        write_to_history(combined_data['org_name'], output_path)
        print(f"Отправили файл {os.path.basename(output_path)} пользователю {user_id}")
        print("Сохранили название и дату для истории")

    except Exception as e:
        print(f"Ошибка при обработке отчета: {e}")
        await update.message.reply_text(f"❌ Ошибка при обработке: {str(e)}")

    finally:
        for f in user_files[user_id].values():
            if os.path.exists(f):
                os.remove(f)
        user_files.pop(user_id, None)

    return ConversationHandler.END


def get_report_conversation_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Создать отчет$"), start_report)],
        states={
            WAITING_WORD: [
                MessageHandler(
                    filters.Document.MimeType("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                    receive_word_file
                )
            ],
            WAITING_FIN: [
                MessageHandler(
                    filters.Document.MimeType("application/pdf"),
                    receive_pdf_file
                )
            ],
            WAITING_EXCEL: [
                MessageHandler(
                    filters.Document.MimeType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") |
                    filters.Document.MimeType("application/vnd.ms-excel"),
                    receive_excel_file
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: ConversationHandler.END)],
    )
