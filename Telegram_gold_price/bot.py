# bot.py
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from telegram.constants import ParseMode
from config import BOT_TOKEN, ADMIN_IDS, MANAGER_NAME, MANAGER_CHAT_ID
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
    """Форматирует цены для сообщение"""
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
    message += f"👉 [НАПИСАТЬ МЕНЕДЖЕРУ](https://t.me/{MANAGER_NAME}) 👈\n\n"

    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name or "Неизвестный пользователь"
    username = update.effective_user.username or "без username"

    # Добавляем пользователя в базу
    db.add_user(user_id)

    # Проверяем, является ли пользователь админом
    if check_admin(user_id):
        # Меню для администратора
        keyboard = [
            [KeyboardButton("💰 Поменять цену")],
            [KeyboardButton("📢 Сделать рассылку")],
            [KeyboardButton("👥 Управление пользователями")]
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
            "Нажмите кнопку ниже, чтобы узнать текущие цены.\n\n"
            f"📞 Для заказа свяжитесь с менеджером: @{MANAGER_NAME}\n"
            "Или просто напишите сообщение прямо мне, и я передам его менеджеру!",
            reply_markup=reply_markup
        )

        # Логируем нового пользователя
        logger.info(f"Новый пользователь: {user_name} (ID: {user_id}, username: @{username})")


# ============ ФУНКЦИИ ДЛЯ ПЕРЕНАПРАВЛЕНИЯ СООБЩЕНИЙ МЕНЕДЖЕРУ ============
def escape_markdown(text):
    """Экранирует специальные символы Markdown V2"""
    if not text:
        return ""
    # Экранируем основные символы Markdown
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


async def forward_to_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перенаправляет сообщения пользователей менеджеру"""
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name or "Неизвестный пользователь"
    username = update.effective_user.username or "без username"

    # Пропускаем администраторов
    if check_admin(user_id):
        return

    # Получаем текст сообщения
    if update.message.text:
        message_text = update.message.text
    elif update.message.caption:
        message_text = update.message.caption
    else:
        message_text = "Сообщение без текста"

    # Создаем сообщение для менеджера
    manager_message = (
        f"📨 *НОВОЕ СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ*\n\n"
        f"👤 *Имя:* {escape_markdown(user_name)}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"📝 *Username:* @{username if username != 'без username' else 'отсутствует'}\n"
        f"📅 *Время:* {update.message.date.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        f"💬 *Сообщение:*\n```\n{escape_markdown(message_text)}\n```\n\n"
    )

    # Добавляем информацию о прикрепленных файлах
    if update.message.photo:
        manager_message += f"📎 *Прикреплено:* {len(update.message.photo)} фото\n"
    if update.message.document:
        doc_name = escape_markdown(
            update.message.document.file_name) if update.message.document.file_name else "Неизвестный файл"
        manager_message += f"📎 *Прикреплен документ:* {doc_name}\n"

    # Создаем инлайн-кнопку для быстрого перехода к диалогу с пользователем
    reply_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"💬 Написать {user_name[:20]} ",
            url=f"tg://user?id={user_id}"
        )]
    ])

    try:
        # Отправляем сообщение менеджеру по chat_id
        await context.bot.send_message(
            chat_id=MANAGER_CHAT_ID,
            text=manager_message,
            parse_mode='Markdown',
            reply_markup=reply_keyboard
        )

        # Уведомляем пользователя
        await update.message.reply_text(
            "✅ Ваше сообщение отправлено менеджеру! Он свяжется с вами в ближайшее время.\n\n"
            f"Также вы можете написать напрямую: @{MANAGER_NAME}"
        )

        logger.info(f"Сообщение от пользователя {user_id} ({user_name}) перенаправлено менеджеру")

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения менеджеру: {e}")

        error_details = str(e)
        logger.error(f"Детали ошибки: {error_details}")

        logger.error(
            f"Пользователь: {user_name} (ID: {user_id}), Время: {update.message.date}, Сообщение: {message_text[:100]}...")

        await update.message.reply_text(
            f"❌ К сожалению, не удалось отправить сообщение автоматически.\n\n"
            f"Пожалуйста, напишите менеджеру напрямую: @{MANAGER_NAME}\n"
            f"Ошибка: {error_details[:100]}..." if len(error_details) > 100 else f"Ошибка: {error_details}"
        )


async def forward_media_to_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перенаправляет медиафайлы менеджеру"""
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name or "Неизвестный пользователь"
    username = update.effective_user.username or "без username"

    # Пропускаем администраторов
    if check_admin(user_id):
        return

    # Создаем текстовое сообщение для менеджера
    manager_message = (
        f"📨 *НОВОЕ МЕДИАСООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ*\n\n"
        f"👤 *Имя:* {escape_markdown(user_name)}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"📝 *Username:* @{username if username != 'без username' else 'отсутствует'}\n"
        f"📅 *Время:* {update.message.date.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
    )

    if update.message.caption:
        manager_message += f"📝 *Подпись:* {escape_markdown(update.message.caption)}\n\n"

    # Создаем инлайн-кнопку для быстрого перехода к диалогу с пользователем
    reply_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"💬 Написать {user_name[:20]} напрямую",
            url=f"tg://user?id={user_id}"
        )]
    ])

    try:
        # Сначала отправляем текстовое сообщение менеджеру
        await context.bot.send_message(
            chat_id=MANAGER_CHAT_ID,
            text=manager_message,
            parse_mode='Markdown',
            reply_markup=reply_keyboard
        )

        # Затем пересылаем само медиа
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=MANAGER_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=f"Фото от @{username if username != 'без username' else 'пользователя'}"
            )
        elif update.message.document:
            await context.bot.send_document(
                chat_id=MANAGER_CHAT_ID,
                document=update.message.document.file_id,
                caption=f"Документ от @{username if username != 'без username' else 'пользователя'}"
            )

        # Уведомляем пользователя
        await update.message.reply_text(
            "✅ Ваши файлы отправлены менеджеру! Он свяжется с вами в ближайшее время.\n\n"
            f"Также вы можете написать напрямую: @{MANAGER_NAME}"
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке медиа менеджеру: {e}")
        logger.error(f"Детали ошибки: {str(e)}")

        await update.message.reply_text(
            f"❌ К сожалению, не удалось отправить файлы автоматически.\n\n"
            f"Пожалуйста, напишите менеджеру напрямую: @{MANAGER_NAME}"
        )


# ============ ФУНКЦИИ ДЛЯ АДМИНИСТРАТОРА ============

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора!")
        return

    keyboard = [
        [KeyboardButton("💰 Поменять цену")],
        [KeyboardButton("📢 Сделать рассылку")],
        [KeyboardButton("👥 Управление пользователями")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def admin_manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление пользователями - показать список и удалять"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора!")
        return

    users = db.get_all_users()

    if not users:
        await update.message.reply_text("📭 Список пользователей пуст.")
        return

    # Формируем список пользователей
    user_list = "📋 *Список пользователей:*\n\n"
    for i, user_id in enumerate(users, 1):
        user_list += f"{i}. ID: `{user_id}`\n"

    user_list += "\n💡 *Чтобы удалить пользователя:*\n"
    user_list += "Отправьте команду:\n`/remove_user ID`\n\n"
    user_list += "📝 *Пример:*\n`/remove_user 123456789`"

    await update.message.reply_text(user_list, parse_mode='Markdown')


async def admin_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление пользователя по ID (только для админов)"""
    if not check_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав администратора!")
        return

    # Проверяем, передан ли ID пользователя
    if not context.args:
        await update.message.reply_text(
            "❌ *Не указан ID пользователя*\n\n"
            "Используйте: `/remove_user 123456789`\n"
            "Чтобы посмотреть список пользователей, нажмите '👥 Управление пользователями'",
            parse_mode='Markdown'
        )
        return

    # Удаляем пользователя
    try:
        user_id = int(context.args[0])

        # Проверяем, не пытается ли админ удалить сам себя
        if user_id == update.effective_user.id:
            await update.message.reply_text(
                "⚠️ Вы не можете удалить сами себя из списка рассылки!",
                parse_mode='Markdown'
            )
            return

        if db.remove_user(user_id):
            await update.message.reply_text(
                f"✅ *Пользователь успешно удален!*\n\n"
                f"🆔 ID: `{user_id}`\n"
                f"📊 Осталось пользователей: {len(db.get_all_users())}",
                parse_mode='Markdown'
            )
            logger.info(f"Администратор {update.effective_user.id} удалил пользователя {user_id}")
        else:
            await update.message.reply_text(
                f"❌ *Пользователь не найден*\n\n"
                f"🆔 ID: `{user_id}` не найден в базе данных.\n\n"
                f"Используйте '👥 Управление пользователями' чтобы посмотреть список.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "❌ *Неверный формат ID*\n\n"
            "ID должен состоять только из цифр.\n"
            "Пример: `/remove_user 123456789`",
            parse_mode='Markdown'
        )


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

    # Получаем текущие цены
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
                    filters.Regex(
                        "^(💰 Цена золота с НДС|💰 Цена золота без НДС|💰 Цена серебра с НДС|💰 Цена серебра без НДС|❌ Отмена)$"),
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

    # Обработчики для администратора
    application.add_handler(MessageHandler(filters.Regex("^📢 Сделать рассылку$"), admin_broadcast))
    application.add_handler(MessageHandler(filters.Regex("^👥 Управление пользователями$"), admin_manage_users))
    application.add_handler(CommandHandler("remove_user", admin_remove_user))
    application.add_handler(CommandHandler("users", admin_manage_users))  # Альтернативная команда

    # Обработчик для пользователей
    application.add_handler(MessageHandler(filters.Regex("^💰 Узнать актуальную цену$"), user_get_price))

    # Обработчик для возврата в меню админа
    application.add_handler(CommandHandler("menu", admin_menu))

    # ОБРАБОТЧИК ДЛЯ ПЕРЕНАПРАВЛЕНИЯ СООБЩЕНИЙ МЕНЕДЖЕРУ
    # Обработчик текстовых сообщений (исключая команды и кнопки)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND &
        ~filters.Regex("^💰 Поменять цену$") &
        ~filters.Regex("^📢 Сделать рассылку$") &
        ~filters.Regex("^👥 Управление пользователями$") &
        ~filters.Regex("^💰 Узнать актуальную цену$") &
        ~filters.Regex("^❌ Отмена$"),
        forward_to_manager
    ))

    # Обработчик медиафайлов (фото, документы)
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.Document.ALL,
        forward_media_to_manager
    ))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == '__main__':
    main()