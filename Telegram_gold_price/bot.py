# bot.py
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from config import BOT_TOKEN, ADMIN_IDS, MANAGER_NAME
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler (теперь 4 состояния для 4-х видов цен)
(
    SELECT_METAL,
    SET_GOLD_PRICE_NDS,
    SET_GOLD_PRICE_NO_NDS,
    SET_SILVER_PRICE_NDS,
    SET_SILVER_PRICE_NO_NDS
) = range(5)

# Инициализация базы данных
db = Database()


# ============ ОБЩИЕ ФУНКЦИИ ============

def check_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


def format_prices():
    """Форматирует цены для сообщения"""
    gold_price_NDS = db.get_gold_price_NDS()
    gold_price_no_NDS = db.get_gold_price_no_NDS()
    silver_price_NDS = db.get_silver_price_NDS()
    silver_price_no_NDS = db.get_silver_price_no_NDS()

    message = "💰 *Добрый день! Предлагаем аффинированный металл в гранулах 999,9:*\n\n"

    if gold_price_NDS > 0:
        message += f"• Золото c НДС: *{gold_price_NDS}* руб./г\n"
    else:
        message += "• Золото c НДС: *нет в продаже*\n"

    if gold_price_no_NDS > 0:
        message += f"• Золото без НДС: *{gold_price_no_NDS}* руб./г\n"
    else:
        message += "• Золото без НДС: *нет в продаже*\n"

    if silver_price_NDS > 0:
        message += f"• Серебро c НДС: *{silver_price_NDS}* руб./г\n"
    else:
        message += "• Серебро c НДС: *нет в продаже*\n"

    if silver_price_no_NDS > 0:
        message += f"• Серебро без НДС: *{silver_price_no_NDS}* руб./г\n"
    else:
        message += "• Серебро без НДС: *нет в продаже*\n"

    # Добавляем информацию о менеджере
    message += "\n📞 *Для заказа можно*\n"
    message += f"👉 [НАПИСАТЬ МЕНЕДЖЕРУ](https://t.me/{MANAGER_NAME}) 👈"

    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id

    # Добавляем пользователя в базу
    db.add_user(user_id)

    # Проверяем, является ли пользователь админом
    if check_admin(user_id):
        # Меню для администратора
        keyboard = [
            [KeyboardButton("💰 Поменять цену")],
            [KeyboardButton("📢 Сделать рассылку")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "👑 Вы вошли как администратор. Выберите действие:",
            reply_markup=reply_markup
        )
    else:
        # Меню для обычного пользователя
        keyboard = [[KeyboardButton("💰 Узнать актуальную цену")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "👋 Добро пожаловать! Я бот для отслеживания цен на драгоценные металлы.\n\n"
            "Нажмите кнопку ниже, чтобы узнать текущие цены.",
            reply_markup=reply_markup
        )


# ============ ФУНКЦИИ ДЛЯ АДМИНИСТРАТОРА ============

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора!")
        return

    keyboard = [
        [KeyboardButton("💰 Поменять цену")],
        [KeyboardButton("📢 Сделать рассылку")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def admin_change_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало изменения цены - выбор металла"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора!")
        return ConversationHandler.END

    keyboard = [
        [KeyboardButton("💰 Цена золота с НДС")],
        [KeyboardButton("💰 Цена золота без НДС")],
        [KeyboardButton("💰 Цена серебра с НДС")],
        [KeyboardButton("💰 Цена серебра без НДС")],
        [KeyboardButton("❌ Отмена")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Получаем текущие цены (используем GET методы, а не SET!)
    gold_price_nds = db.get_gold_price_NDS()
    gold_price_no_nds = db.get_gold_price_no_NDS()
    silver_price_nds = db.get_silver_price_NDS()
    silver_price_no_nds = db.get_silver_price_no_NDS()

    await update.message.reply_text(
        f"📊 *Текущие цены:*\n\n"
        f"• Золото c НДС: {gold_price_nds if gold_price_nds > 0 else 'нет в продаже'} руб./г\n"
        f"• Золото без НДС: {gold_price_no_nds if gold_price_no_nds > 0 else 'нет в продаже'} руб./г\n"
        f"• Серебро с НДС: {silver_price_nds if silver_price_nds > 0 else 'нет в продаже'} руб./г\n"
        f"• Серебро без НДС: {silver_price_no_nds if silver_price_no_nds > 0 else 'нет в продаже'} руб./г\n\n"
        f"Выберите тип цены для изменения (0 - нет в продаже):",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_METAL


async def admin_select_metal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор металла для изменения цены"""
    text = update.message.text

    if text == "💰 Цена золота с НДС":
        await update.message.reply_text(
            "💰 Введите новую цену на золото с НДС (в рублях за грамм):\n\n"
            "Пример: 5250.50\n"
            "0 - нет в продаже\n"
            "Для отмены введите /cancel"
        )
        return SET_GOLD_PRICE_NDS

    elif text == "💰 Цена золота без НДС":
        await update.message.reply_text(
            "💰 Введите новую цену на золото без НДС (в рублях за грамм):\n\n"
            "Пример: 5250.50\n"
            "0 - нет в продаже\n"
            "Для отмены введите /cancel"
        )
        return SET_GOLD_PRICE_NO_NDS

    elif text == "💰 Цена серебра с НДС":
        await update.message.reply_text(
            "💰 Введите новую цену на серебро с НДС (в рублях за грамм):\n\n"
            "Пример: 65.75\n"
            "0 - нет в продаже\n"
            "Для отмены введите /cancel"
        )
        return SET_SILVER_PRICE_NDS

    elif text == "💰 Цена серебра без НДС":
        await update.message.reply_text(
            "💰 Введите новую цену на серебро без НДС (в рублях за грамм):\n\n"
            "Пример: 65.75\n"
            "0 - нет в продаже\n"
            "Для отмены введите /cancel"
        )
        return SET_SILVER_PRICE_NO_NDS

    elif text == "❌ Отмена":
        await admin_menu(update, context)
        return ConversationHandler.END


async def admin_set_gold_price_nds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка цены на золото с НДС"""
    try:
        price = float(update.message.text.replace(',', '.'))

        if price < 0:
            await update.message.reply_text("❌ Цена не может быть отрицательной!")
            return SET_GOLD_PRICE_NDS

        if db.set_gold_price_NDS(price):
            if price > 0:
                await update.message.reply_text(f"✅ Цена на золото с НДС успешно обновлена: {price} руб./г")
            else:
                await update.message.reply_text("✅ Золото с НДС отмечено как 'нет в продаже'")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении цены!")

    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректное число!")
        return SET_GOLD_PRICE_NDS

    await admin_menu(update, context)
    return ConversationHandler.END


async def admin_set_gold_price_no_nds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка цены на золото без НДС"""
    try:
        price = float(update.message.text.replace(',', '.'))

        if price < 0:
            await update.message.reply_text("❌ Цена не может быть отрицательной!")
            return SET_GOLD_PRICE_NO_NDS

        if db.set_gold_price_no_NDS(price):
            if price > 0:
                await update.message.reply_text(f"✅ Цена на золото без НДС успешно обновлена: {price} руб./г")
            else:
                await update.message.reply_text("✅ Золото без НДС отмечено как 'нет в продаже'")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении цены!")

    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректное число!")
        return SET_GOLD_PRICE_NO_NDS

    await admin_menu(update, context)
    return ConversationHandler.END


async def admin_set_silver_price_nds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка цены на серебро с НДС"""
    try:
        price = float(update.message.text.replace(',', '.'))

        if price < 0:
            await update.message.reply_text("❌ Цена не может быть отрицательной!")
            return SET_SILVER_PRICE_NDS

        if db.set_silver_price_NDS(price):
            if price > 0:
                await update.message.reply_text(f"✅ Цена на серебро с НДС успешно обновлена: {price} руб./г")
            else:
                await update.message.reply_text("✅ Серебро с НДС отмечено как 'нет в продаже'")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении цены!")

    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректное число!")
        return SET_SILVER_PRICE_NDS

    await admin_menu(update, context)
    return ConversationHandler.END


async def admin_set_silver_price_no_nds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка цены на серебро без НДС"""
    try:
        price = float(update.message.text.replace(',', '.'))

        if price < 0:
            await update.message.reply_text("❌ Цена не может быть отрицательной!")
            return SET_SILVER_PRICE_NO_NDS

        if db.set_silver_price_no_NDS(price):
            if price > 0:
                await update.message.reply_text(f"✅ Цена на серебро без НДС успешно обновлена: {price} руб./г")
            else:
                await update.message.reply_text("✅ Серебро без НДС отмечено как 'нет в продаже'")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении цены!")

    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректное число!")
        return SET_SILVER_PRICE_NO_NDS

    await admin_menu(update, context)
    return ConversationHandler.END


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Сделать рассылку' для админа"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора!")
        return

    message = format_prices()

    users = db.get_all_users()
    success_count = 0
    error_count = 0

    await update.message.reply_text(f"📤 Начинаю рассылку для {len(users)} пользователей...")

    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")
            error_count += 1

    await update.message.reply_text(
        f"✅ Рассылка завершена!\n"
        f"Успешно отправлено: {success_count}\n"
        f"Не удалось отправить: {error_count}"
    )


# ============ ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЯ ============

async def user_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Узнать актуальную цену' для пользователя"""
    message = format_prices()
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    if check_admin(update.effective_user.id):
        await admin_menu(update, context)
    else:
        keyboard = [[KeyboardButton("💰 Узнать актуальную цену")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Операция отменена.", reply_markup=reply_markup)

    return ConversationHandler.END


# ============ ОСНОВНАЯ ФУНКЦИЯ ============

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler для изменения цен
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Поменять цену$"), admin_change_price_start)],
        states={
            SELECT_METAL: [
                MessageHandler(
                    filters.Regex("^(💰 Цена золота с НДС|💰 Цена золота без НДС|💰 Цена серебра с НДС|💰 Цена серебра без НДС|❌ Отмена)$"),
                    admin_select_metal
                )
            ],
            SET_GOLD_PRICE_NDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_gold_price_nds)
            ],
            SET_GOLD_PRICE_NO_NDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_gold_price_no_nds)
            ],
            SET_SILVER_PRICE_NDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_silver_price_nds)
            ],
            SET_SILVER_PRICE_NO_NDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_silver_price_no_nds)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="price_change_conversation"
    )

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    # Обработчик рассылки
    application.add_handler(MessageHandler(filters.Regex("^📢 Сделать рассылку$"), admin_broadcast))

    # Обработчик для пользователей
    application.add_handler(MessageHandler(filters.Regex("^💰 Узнать актуальную цену$"), user_get_price))

    # Обработчик для возврата в меню админа
    application.add_handler(CommandHandler("menu", admin_menu))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == '__main__':
    main()