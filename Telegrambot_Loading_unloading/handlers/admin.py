import asyncio
from datetime import datetime, timedelta, time
from aiogram import F, types, Router, Bot
from aiogram.client import bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import Config
from keyboards.admin_kb import get_admin_keyboard
from keyboards.executor_kb import acquaintance_keyboard
from states import OrderStates
from database import create_task, change_status_user, get_all_users_type

router = Router()

async def send_temp_message(
    bot: Bot,
    chat_id: int,
    text: str,
    delete_after: int = 5  # Через сколько секунд удалить
):
    """Сообщение, которое исчезает. """
    msg = await bot.send_message(chat_id, text)
    await asyncio.sleep(delete_after)
    await bot.delete_message(chat_id, msg.message_id)

# АВТОРИЗАЦИЯ РАБОТНИКА
@router.callback_query(F.data.startswith("add_worker_"))
async def add_worker_callback(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()  # Это уберет индикатор загрузки

    user_id = int(callback.data.split("_")[2])
    # Меняем статус работника на Активный.
    change_status_user(user_id)

    # Отправляем исчезающее сообщение всем администраторам.
    for admin_id in Config.get_admins():
        try:
            text = f"Пользователя {user_id} принял администратор: {callback.from_user.id}"
            # if admin_id != callback.from_user.id:  # Не уведомляем себя
            await send_temp_message(bot, admin_id, text, delete_after=5)
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    # Отправляем одобрившему администратору главное меню
    await bot.send_message(
        chat_id=callback.from_user.id,
        text="Главное меню администратора",
        reply_markup=get_admin_keyboard()
    )

    # Сообщение работнику.
    try:
        worker_message = (
            "Вас добавили. Поработаем! 💪 "
            "Чат-бот поможет вам эффективно работать с заявками "
            "и своевременно получать оплаты. Для начала давайте познакомимся."
        )
        await bot.send_message(
            chat_id=user_id,
            text=worker_message,
            reply_markup=acquaintance_keyboard()
        )
    except Exception as e:
        print(f"Не удалось отправить сообщение работнику {user_id}: {e}")
        for admin_id in Config.get_admins():
            await bot.send_message(
                chat_id=admin_id,
                text=f"⚠ Не удалось отправить приветствие работнику {user_id}"
            )

@router.callback_query(F.data.startswith("ignore_"))
async def ignore_callback(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        text=f"{callback.message.text}\n\n❌ Заявка от пользователя {user_id} проигнорирована",
        reply_markup=None
    )
    await callback.answer("Заявка проигнорирована")
    await callback.message.answer(
        "Добро пожаловать, Администратор!",
        reply_markup=get_admin_keyboard()
    )


# СОЗДАТЬ ЗАКАЗ
@router.message(F.text == "Поставить задачу 📝")
async def create_order(message: types.Message, state: FSMContext):
    # Создаем клавиатуру для выбора типа задачи
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Погрузка"))
    builder.add(types.KeyboardButton(text="Доставка"))
    builder.adjust(2)

    await message.answer(
        "Выбери тип задачи:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(OrderStates.waiting_type_of_task)


@router.message(OrderStates.waiting_type_of_task)
async def process_task_type(message: types.Message, state: FSMContext):
    if message.text not in ["Погрузка", "Доставка"]:
        await message.answer("Пожалуйста, выберите тип задачи из предложенных вариантов")
        return

    await state.update_data(type_of_task=message.text)

    # Создаем клавиатуру с датами (например, на 3 дня вперед)
    builder = ReplyKeyboardBuilder()
    today = datetime.now().date()
    for i in range(3):
        date = today + timedelta(days=i)
        builder.add(types.KeyboardButton(text=date.strftime("%d.%m.%Y")))
    builder.adjust(3)

    await message.answer(
        "Выберите дату назначения:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(OrderStates.waiting_date_of_destination)


@router.message(OrderStates.waiting_date_of_destination)
async def process_date(message: types.Message, state: FSMContext):
    try:
        date_obj = datetime.strptime(message.text, "%d.%m.%Y").date()
        await state.update_data(date_of_destination=date_obj)
    except ValueError:
        await message.answer("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ")
        return

    # Создаем клавиатуру с временными интервалами
    builder = ReplyKeyboardBuilder()
    for hour in range(8, 20, 1):  # С 8 утра до 8 вечера с шагом 1 час
        time_str = f"{hour:02d}:00"
        builder.add(types.KeyboardButton(text=time_str))

    # Применяем adjust только к кнопкам времени (12 кнопок)
    builder.adjust(3)  # 3 кнопки в каждом ряду

    # Добавляем кнопку ручного ввода отдельно
    builder.row(types.KeyboardButton(text="Указать вручную"))

    await message.answer(
        "Выберите время назначения:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(OrderStates.waiting_appointment_time)


@router.message(OrderStates.waiting_appointment_time)
async def process_time(message: types.Message, state: FSMContext):
    if message.text == "Указать вручную":
        await message.answer(
            "Введите время в формате ЧЧ:ММ (например, 11:50):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(OrderStates.waiting_custom_time)
        return

    try:
        # Проверяем формат времени для стандартного выбора
        time_obj = datetime.strptime(message.text, "%H:%M").time()
        await state.update_data(appointment_time=time_obj)
        await proceed_to_description(message, state)
    except ValueError:
        await message.answer("Пожалуйста, выберите время из предложенных вариантов или укажите вручную")


@router.message(OrderStates.waiting_custom_time)
async def process_custom_time(message: types.Message, state: FSMContext):
    try:
        # Проверяем формат времени для ручного ввода
        time_obj = datetime.strptime(message.text, "%H:%M").time()
        await state.update_data(appointment_time=time_obj)
        await proceed_to_description(message, state)
    except ValueError:
        await message.answer("Пожалуйста, введите время в формате ЧЧ:ММ (например, 11:50)")


async def proceed_to_description(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите описание задачи:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderStates.waiting_description)


@router.message(OrderStates.waiting_custom_time)
async def process_custom_time(message: types.Message, state: FSMContext):
    try:
        time_obj = datetime.strptime(message.text, "%H:%M").time()

        # Проверяем что время в рабочем диапазоне (8:00-20:00)
        if time_obj < time(8, 0) or time_obj > time(19, 0):
            await message.answer("Пожалуйста, укажите время между 8:00 и 20:00")
            return

        await state.update_data(appointment_time=time_obj)
        await proceed_to_description(message, state)
    except ValueError:
        await message.answer("Пожалуйста, введите время в формате ЧЧ:ММ (например, 11:50)")


@router.message(OrderStates.waiting_description)
async def process_description(message: types.Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("Описание должно содержать минимум 10 символов")
        return

    await state.update_data(description=message.text)
    await message.answer("Введите основной адрес:")
    await state.set_state(OrderStates.waiting_main_address)


@router.message(OrderStates.waiting_main_address)
async def process_main_address(message: types.Message, state: FSMContext):
    if len(message.text) < 5:
        await message.answer("Адрес слишком короткий")
        return

    await state.update_data(main_address=message.text)
    await message.answer("Введите дополнительный адрес (если нет - напишите 'нет'):")
    await state.set_state(OrderStates.waiting_additional_address)


@router.message(OrderStates.waiting_additional_address)
async def process_additional_address(message: types.Message, state: FSMContext):
    additional_address = None if message.text.lower() == "нет" else message.text
    await state.update_data(additional_address=additional_address)
    await message.answer("Укажите необходимое количество человек (цифрой):")
    await state.set_state(OrderStates.waiting_required_workers)


@router.message(OrderStates.waiting_required_workers)
async def process_required_workers(message: types.Message, state: FSMContext):
    try:
        workers = int(message.text)
        if workers < 1:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число работников (1 и более)")
        return

    await state.update_data(required_workers=workers)
    await message.answer("Укажите цену оплаты на одного человека (в рублях):")
    await state.set_state(OrderStates.waiting_worker_price)  # Переходим к запросу цены


@router.message(OrderStates.waiting_worker_price)
async def process_worker_price(message: types.Message, state: FSMContext, bot: Bot):
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (например: 1000 или 1500.50)")
        return

    await state.update_data(worker_price=price)
    data = await state.get_data()

    try:
        # Сохраняем задачу в базу данных
        task_id = create_task(data)
    except Exception as e:
        await message.answer("Произошла ошибка при создании задачи. Попробуйте позже.")
        print(f"Error creating task: {e}")

    # Формируем сообщение о новой задаче
    task_message = (
        f"📌 Новая задача № {task_id}!\n"
        f"👷🚛Тип: {data['type_of_task']}\n"
        f"📅 Дата: {data['date_of_destination'].strftime('%d.%m.%Y')}\n"
        f"🕒 Время: {data['appointment_time'].strftime('%H:%M')}\n"
        f"🏠 Адрес: {data['main_address']}\n"
        f"👥 Кол-во человек: {data['required_workers']}\n"
        f"💸 Оплата: {price} руб./чел.\n"
        f"📄 Описание: {data['description']}"
    )

    # Получаем всех активных пользователей связанных с текущим видом задачи.
    # Водителей или грузчиков.
    user_ids = get_all_users_type(data['type_of_task'])
    print(f"Список исполнителей: ")

    # Рассылаем задачу погрузку - грузчикам, доставку - водителям.
    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=task_message
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    # Отправляем подтверждение создателю
    await message.answer(
        f"✅ Задача #{task_id} успешно создана и отправлена {len(user_ids)} исполнителям!\n"
        f"{task_message}"
    )

    await state.clear()
