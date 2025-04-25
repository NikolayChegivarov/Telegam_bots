from datetime import datetime, timedelta, time
from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from keyboards.admin_kb import get_admin_keyboard
from states import OrderStates
from database import create_task

router = Router()


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

    # Создаем клавиатуру с временными интервалами и кнопкой ручного ввода
    builder = ReplyKeyboardBuilder()
    for hour in range(8, 20, 2):  # С 8 утра до 8 вечера с шагом 2 часа
        time_str = f"{hour:02d}:00"
        builder.add(types.KeyboardButton(text=time_str))

    # Добавляем кнопку ручного ввода
    builder.add(types.KeyboardButton(text="Указать вручную"))
    builder.adjust(3, 1)  # 3 кнопки в ряду, затем "Указать вручную" отдельно

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
async def process_worker_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (например: 1000 или 1500.50)")
        return

    await state.update_data(worker_price=price)

    # Получаем все данные из состояния
    data = await state.get_data()

    try:
        # Сохраняем задачу в базу данных
        task_id = create_task({
            'date_of_destination': data['date_of_destination'],
            'appointment_time': data['appointment_time'],
            'type_of_task': data['type_of_task'],
            'description': data['description'],
            'main_address': data['main_address'],
            'additional_address': data['additional_address'],
            'required_workers': data['required_workers'],
            'worker_price': data['worker_price']  # Передаем цену из данных состояния
        })

        await message.answer(
            f"✅ Задача успешно создана!\n"
            f"ID задачи: {task_id}\n"
            f"Тип: {data['type_of_task']}\n"
            f"Дата: {data['date_of_destination'].strftime('%d.%m.%Y')}\n"
            f"Время: {data['appointment_time'].strftime('%H:%M')}\n"
            f"Адрес: {data['main_address']}\n"
            f"Доп. адрес: {data['additional_address'] or 'нет'}\n"
            f"Кол-во человек: {data['required_workers']}\n"
            f"Оплата одному человеку: {data['worker_price']} руб."
        )
        await message.answer("Работаем дальше!",
                             reply_markup=get_admin_keyboard())
    except Exception as e:
        await message.answer("Произошла ошибка при создании задачи. Попробуйте позже.")
        print(f"Error creating task: {e}")

    await state.clear()

