from telegram import Update
from telegram.ext import ContextTypes
from database.database_interaction import DatabaseInteraction
from keyboards import (
    get_admin_keyboard,
    get_user_keyboard,
    get_blocked_keyboard,
    administrative_keyboard,
    get_auth_keyboard,
)


# ▶️ Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseInteraction()
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name
    last_name = user.last_name or ""

    print(f"Пользователь {user_id} начал взаимодействие с ботом")

    try:
        if not db.user_exists(user_id):
            # Пользователь не существует в БД
            if db.is_admin(user_id):
                # Если администратор добавляем в бд, даем "Активный"
                db.add_user(user_id, first_name, last_name)
                db.update_user_status(user_id, "Активный")
                await update.message.reply_text(
                    "Вы добавлены как администратор.",
                    reply_markup=get_admin_keyboard()
                )
            else:
                # Если новый пользователь.
                await update.message.reply_text(
                    "Привет. Я бот для заполнения шаблона юридической информацией. "
                    "Для авторизации нажмите АВТОРИЗОВАТЬСЯ.",
                    reply_markup=get_blocked_keyboard()
                )
            return

        # Пользователь есть в БД

        # Проверка на админа
        if db.is_admin(user_id):
            await update.message.reply_text(
                "Добро пожаловать, администратор.",
                reply_markup=get_admin_keyboard()
            )
            return

        status = db.check_user_status(user_id)

        if status == "Активный":
            await update.message.reply_text(
                "Добро пожаловать! Вы можете приступить к работе.",
                reply_markup=get_user_keyboard()
            )
        elif status == "В ожидании":
            await update.message.reply_text(
                "Вы уже отправляли заявку. Ожидайте подтверждения от администратора."
            )
        elif status == "Заблокированный":
            await update.message.reply_text(
                "❌ Вам ограничили доступ к сервису."
            )
        else:
            await update.message.reply_text(
                "⚠️ Неизвестный статус. Обратитесь к администратору."
            )
    except Exception as e:
        print(f"Ошибка в start: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    finally:
        db.close()


# 👤 Пользователь нажал кнопку "Авторизоваться"
async def handle_authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие пользователем кнопки 'Авторизоваться'.

    - Проверяет, зарегистрирован ли пользователь в базе данных.
    - Если пользователь новый, добавляет его в базу с дефолтным статусом "в ожидании".
    - Если пользователь уже подал заявку, уведомляет, что запрос рассматривается.
    """
    db = DatabaseInteraction()
    user = update.effective_user
    user_id = user.id

    try:
        print(f"Пользователь {user_id} нажал 'Авторизоваться'")
        if not db.check_user_status(user_id):
            db.add_user(user_id, user.first_name, user.last_name or "")
            await update.message.reply_text("Ваш запрос находится на согласовании у администратора бота")
        else:
            await update.message.reply_text("Ваш запрос уже находится на рассмотрении")
    except Exception as e:
        print(f"Ошибка в handle_authorize: {e}")
    finally:
        db.close()


# ✅ "Добавить сотрудника"
async def handle_auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """После проверки прав,
    изменяет статус сотрудника на 'Активный'"""
    query = update.callback_query
    await query.answer() # подтверждает нажатие
    admin_id = query.from_user.id

    try:
        if query.data.startswith('auth_'):
            user_id = int(query.data.split('_')[1])
            db = DatabaseInteraction()

            if db.is_admin(admin_id):
                db.update_user_status(user_id, 'Активный')
                await query.edit_message_text(f"Пользователь {user_id} успешно авторизован!")
            else:
                await query.edit_message_text("У вас нет прав для этого действия.")
            db.close()
    except Exception as e:
        print(f"Ошибка в handle_auth_callback: {e}")


# 👥 Авторизация сотрудников (выбор из списка)
async def add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseInteraction()
    admin_id = update.effective_user.id

    try:
        print(f"Администратор {admin_id} запросил добавление сотрудника")
        if db.is_admin(admin_id):
            blocked_users = db.get_blocked_users()
            if blocked_users:
                keyboard = get_auth_keyboard(blocked_users)
                await update.message.reply_text("Выберите пользователя для авторизации:", reply_markup=keyboard)
            else:
                await update.message.reply_text("Нет пользователей, ожидающих авторизации.")
        else:
            await update.message.reply_text("У вас нет прав для этого действия.")
    except Exception as e:
        print(f"Ошибка в add_employee: {e}")
    finally:
        db.close()
