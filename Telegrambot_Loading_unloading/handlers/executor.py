import psycopg2
from psycopg2 import extras
from aiogram import Router, types, F, Bot

from config import Config
from database import get_pending_tasks, get_connection
from keyboards.executor_kb import get_executor_keyboard
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(F.text == "Хочу работать! 🤝")
async def get_executor_authorization(message: types.Message, state: FSMContext, bot: Bot):
    # Получаем информацию о пользователе
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    username = f"@{message.from_user.username}" if message.from_user.username else "нет"

    # Формируем сообщение для админов
    admin_message = (
        "Новая заявка на работу!\n\n"
        f"ID пользователя: {user_id}\n"
        f"Имя: {first_name}\n"
        f"Фамилия: {last_name}\n"
        f"Username: {username}\n\n"
        "Пожалуйста, обработайте заявку."
    )

    # Отправляем сообщение всем админам
    for admin_id in Config.get_admins():
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    await message.answer("Ваша заявка отправлена администраторам. Мы свяжемся с вами в ближайшее время!")



@router.message(F.text == "Список активных задач 📋")
async def all_order_executor(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    connection = None
    cursor = None

    try:
        # Получаем информацию о пользователе из БД
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute("SELECT is_loader, is_driver FROM users WHERE id_users = %s", (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            await message.answer("Пользователь не найден.")
            return

        is_loader = user_data['is_loader']
        is_driver = user_data['is_driver']

        # Определяем тип пользователя для фильтрации задач
        user_type = None
        if is_loader and not is_driver:
            user_type = "loader"
        elif is_driver and not is_loader:
            user_type = "driver"
        # Если пользователь и грузчик и водитель, показываем все задачи

        # Получаем задачи с учетом типа пользователя
        tasks = get_pending_tasks(user_type)

        if not tasks:
            await message.answer("Нет активных задач для вас.")
            return

        # Формируем сообщение с задачами
        response = []
        for task in tasks:
            task_info = (
                f"🔹 Тип: {task['task_type']}\n"
                f"📅 Дата: {task['date']}\n"
                f"⏰ Время: {task['time']}\n"
                f"📍 Адрес: {task['main_address']}"
            )
            if task['additional_address']:
                task_info += f" ({task['additional_address']})"
            task_info += (
                f"\n📝 Описание: {task['description']}\n"
                f"👷 Требуется работников: {task['required_workers']}\n"
                f"💰 Цена за работу: {task['worker_price']} руб.\n"
                f"────────────────────"
            )
            response.append(task_info)

        await message.answer("Активные задачи:\n\n" + "\n\n".join(response))

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

@router.message(F.text == "Взять задачу ➡️")
async def create_order(message: types.Message, state: FSMContext):
    pass

@router.message(F.text == "Личный кабинет 👨‍💻")
async def create_order(message: types.Message, state: FSMContext):
    pass