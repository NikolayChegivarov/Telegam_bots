# Отчеты
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import reports, get_history_period_keyboard
from database.history_manager import read_history


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
    """Предоставляет отчеты за выбранный период (1, 2 или 3 месяца)."""
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
        if history:
            response_lines = [
                f"• {org} — {created_at.strftime('%d.%m.%Y')} ({file_path})"
                for org, file_path, created_at in history
            ]
            response = "История отчетов:\n\n" + "\n".join(response_lines)
        else:
            response = "Отчеты за выбранный период отсутствуют."
        await update.message.reply_text(response)
    except Exception as e:
        print(f"Ошибка в handle_history_period: {e}")
        await update.message.reply_text("Произошла ошибка при получении истории.")

async def make_a_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реагирует на 'Извлечь отчет'
    """


