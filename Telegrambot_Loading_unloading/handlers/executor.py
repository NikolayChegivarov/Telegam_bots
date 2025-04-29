import asyncio

import psycopg2
from aiogram.client import bot
from psycopg2 import extras
from aiogram import Router, types, F, Bot

from config import Config
from database import get_pending_tasks, get_connection, connect_to_database, add_to_assigned_performers, get_user_tasks, \
    my_data, contractor_statistics, dell_to_assigned_performers
from aiogram.fsm.context import FSMContext

from handlers.admin import send_temp_message
from keyboards.admin_kb import authorization_keyboard
from keyboards.executor_kb import yes_no_keyboard, get_executor_keyboard, personal_office_keyboard, update_data, support
from states import UserRegistration, TaskNumber
from validation import validate_phone, validate_inn

router = Router()

# ЗАПУСКАЕМ ПРОЦЕСС АВТОРИЗАЦИИ.
@router.message(F.text == "Хочу работать! 👷")
async def get_executor_authorization(message: types.Message, bot: Bot):
    print("нажали Хочу работать")
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
                text=admin_message,
                reply_markup=authorization_keyboard(user_id)
            )
            print(f"Отправили сообщение админу {admin_id} ")
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    await message.answer("Ваша заявка отправлена администраторам. Мы свяжемся с вами в ближайшее время!")

# СОБИРАЕМ/ОБНОВЛЯЕМ ДАННЫЕ РАБОТНИКА
@router.message(F.text.in_(["Начать знакомство 🤝", "Обновить данные 🤝"]))
async def start_registration(message: types.Message, state: FSMContext):
    await state.set_state(UserRegistration.first_name)
    await message.answer(
        "Введите ваше имя:",
        reply_markup=types.ReplyKeyboardRemove()  # Удаляет текущую клавиатуру
    )

@router.message(UserRegistration.first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(UserRegistration.last_name)
    await message.answer("Введите вашу фамилию:")

@router.message(UserRegistration.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(UserRegistration.phone)
    await message.answer("Введите ваш телефон (например, 79161234567 или +7 916 123 45 67):")

@router.message(UserRegistration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer("Некорректный формат телефона. Пожалуйста, введите телефон еще раз:")
        return

    await state.update_data(phone=message.text)
    await state.set_state(UserRegistration.is_loader)
    await message.answer("Вы грузчик?", reply_markup=yes_no_keyboard)

@router.message(UserRegistration.is_loader, F.text.in_(["Да", "Нет"]))
async def process_is_loader(message: types.Message, state: FSMContext):
    is_loader = message.text == "Да"
    await state.update_data(is_loader=is_loader)
    await state.set_state(UserRegistration.is_driver)
    await message.answer("Вы водитель?", reply_markup=yes_no_keyboard)

@router.message(UserRegistration.is_driver, F.text.in_(["Да", "Нет"]))
async def process_is_driver(message: types.Message, state: FSMContext):
    is_driver = message.text == "Да"
    await state.update_data(is_driver=is_driver)
    await state.set_state(UserRegistration.is_self_employed)
    await message.answer("Вы самозанятый?", reply_markup=yes_no_keyboard)

@router.message(UserRegistration.is_self_employed, F.text.in_(["Да", "Нет"]))
async def process_is_self_employed(message: types.Message, state: FSMContext, bot: Bot):
    is_self_employed = message.text == "Да"
    await state.update_data(is_self_employed=is_self_employed)

    if is_self_employed:
        await state.set_state(UserRegistration.inn)
        await message.answer("Введите ваш ИНН (10 или 12 цифр):", reply_markup=types.ReplyKeyboardRemove())
    else:
        await complete_registration(message, state, bot)

@router.message(UserRegistration.inn)
async def process_inn(message: types.Message, state: FSMContext, bot: Bot):
    if not validate_inn(message.text):
        await message.answer("Некорректный ИНН. Пожалуйста, введите 10 или 12 цифр:")
        return

    await state.update_data(inn=message.text)
    await complete_registration(message, state, bot)

async def complete_registration(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()

    # Получаем данные из состояния
    first_name = user_data.get('first_name', '')
    last_name = user_data.get('last_name', '')
    phone = user_data.get('phone', '')
    is_loader = user_data.get('is_loader', False)
    is_driver = user_data.get('is_driver', False)
    is_self_employed = user_data.get('is_self_employed', False)
    inn = user_data.get('inn', None)
    user_id = message.from_user.id

    try:
        with connect_to_database() as connection:
            if not connection:
                await message.answer("Ошибка подключения к базе данных. Пожалуйста, попробуйте позже.")
                return False

            with connection.cursor() as cursor:
                # Проверяем, существует ли уже пользователь
                cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (user_id,))
                user_exists = cursor.fetchone()

                if user_exists:
                    # Обновляем существующего пользователя
                    cursor.execute("""
                        UPDATE users 
                        SET first_name = %s,
                            last_name = %s,
                            phone = %s,
                            is_loader = %s,
                            is_driver = %s,
                            is_self_employed = %s,
                            inn = %s
                        WHERE id_user_telegram = %s
                    """, (
                        first_name,
                        last_name,
                        phone,
                        is_loader,
                        is_driver,
                        is_self_employed,
                        inn,
                        user_id
                    ))
                else:
                    # Создаем нового пользователя
                    cursor.execute("""
                        INSERT INTO users (
                            id_user_telegram,
                            first_name,
                            last_name,
                            phone,
                            is_loader,
                            is_driver,
                            is_self_employed,
                            inn
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        first_name,
                        last_name,
                        phone,
                        is_loader,
                        is_driver,
                        is_self_employed,
                        inn
                    ))

                connection.commit()

        # Формируем текст для администраторов
        admin_text = (
            "🆕 Появились новые данные:\n"
            f"👤 ID: {user_id}\n"
            f"👨‍💼 Имя: {first_name} {last_name}\n"
            f"📞 Телефон: {phone}\n"
            f"🏗 Грузчик: {'✅ Да' if is_loader else '❌ Нет'}\n"
            f"🚚 Водитель: {'✅ Да' if is_driver else '❌ Нет'}\n"
            f"💼 Самозанятый: {'✅ Да' if is_self_employed else '❌ Нет'}\n"
            f"{'📝 ИНН: ' + inn if is_self_employed else ''}"
        )

        # Рассылаем всем админам
        for admin_id in Config.get_admins():
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_text
                )
            except Exception as e:
                print(f"Не удалось отправить сообщение администратору {admin_id}: {e}")

        # Отправляем сообщение пользователю с клавиатурой главного меню
        await message.answer(
            "✅ Регистрация завершена!\n"
            f"👤 Ваше имя: {first_name} {last_name}\n"
            f"📞 Ваш телефон: {phone}\n"
            f"🏗 Грузчик: {'✅ Да' if is_loader else '❌ Нет'}\n"
            f"🚚 Водитель: {'✅ Да' if is_driver else '❌ Нет'}\n"
            f"💼 Самозанятый: {'✅ Да' if is_self_employed else '❌ Нет'}\n"
            f"{'📝 Ваш ИНН: ' + inn if is_self_employed else ''}\n\n"
            "Теперь вам доступны все функции бота!",
            reply_markup=get_executor_keyboard()
        )

        return True

    except Exception as e:
        await message.answer(f"Произошла ошибка при сохранении данных: {str(e)}")
        return False
    finally:
        await state.clear()


# СМОТРИМ АКТИВНЫЕ ЗАДАЧИ
@router.message(F.text == "Список активных задач 📋")
async def all_order_executor(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Получаем информацию о пользователе из БД
                cursor.execute("SELECT is_loader, is_driver FROM users WHERE id_user_telegram = %s", (user_id,))
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

                # Получаем задачи с учетом типа пользователя
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE status = 'pending' 
                    AND (task_type = %s OR %s IS NULL)
                    ORDER BY created_at DESC
                """, (user_type, user_type))
                tasks = cursor.fetchall()

                if not tasks:
                    await message.answer("Нет активных задач для вас.")
                    return

                # Формируем сообщение с задачами
                response = []
                for task in tasks:
                    task_info = (
                        f"🆔 Номер задачи: {task['id_tasks']}\n"
                        f"🔹 Тип: {task['task_type']}\n"
                        f"📅 Дата: {task['date']}\n"
                        f"⏰ Время: {task['time']}\n"
                        f"🏡 Адрес: {task['main_address']}"
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
        await message.answer(f"Произошла ошибка: {str(e)}")


# ВЗЯТЬ ЗАДАЧУ
@router.message(F.text == "Взять задачу ➡️")
async def take_the_task(message: types.Message, state: FSMContext):
    await state.set_state(TaskNumber.waiting_task_number_add)
    await message.answer("Введите номер задачи которую хотите взять:")

@router.message(TaskNumber.waiting_task_number_add)
async def get_a_task(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    task_text = message.text

    # Проверяем, что введен номер задачи (число)
    if not task_text.isdigit():
        await message.answer("Номер задачи должен быть числом. Попробуйте еще раз.")
        return

    id_tasks = int(task_text)
    status = add_to_assigned_performers(user_id, id_tasks)
    print(f"status {status}")
    await message.answer(
        text=status,
        reply_markup=get_executor_keyboard(),
    )
    await state.clear()

# ОТКАЗАТЬСЯ ОТ ЗАДАЧИ
@router.message(F.text == "Отказаться от задачи ❌")
async def refusal_of_the_task(message: types.Message, state: FSMContext):
    await state.set_state(TaskNumber.waiting_task_number_dell)
    await message.answer("Введите номер задачи от которой хотите отказаться:")

@router.message(TaskNumber.waiting_task_number_dell)
async def refusal_of_the_task_2(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    task_text = message.text

    # Проверяем, что введен номер задачи (число)
    if not task_text.isdigit():
        await message.answer("Номер задачи должен быть числом. Попробуйте еще раз.")
        return

    id_tasks = int(task_text)
    status = dell_to_assigned_performers(user_id, id_tasks)
    print(f"status {status}")
    await message.answer(
        text=status,
        reply_markup=get_executor_keyboard(),
    )
    await state.clear()

# ОТЧИТАТЬСЯ
@router.message(F.text == "Заявка выполнена ✅")
async def application_is_completed(message: types.Message, state: FSMContext):
    await state.set_state(TaskNumber.waiting_task_number_report)
    await message.answer("Введите номер задачи которую выполнили:")

@router.message(TaskNumber.waiting_task_number_report)
async def application_is_completed_2(message: types.Message, state: FSMContext, bot: Bot):  # Добавляем bot в параметры
    user_id = message.from_user.id
    task_text = message.text
    # Отправляем исчезающее сообщение всем администраторам.
    for admin_id in Config.get_admins():
        try:
            text = f"Пользователь {user_id} уведомляет о выполнении задачи # {task_text}"
            await send_temp_message(bot, admin_id, text, delete_after=10)
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")


@router.message(F.text == "Личный кабинет 👨‍💻")
async def personal_office(message: types.Message, state: FSMContext):
    await message.answer(
        text="Выберите необходимые опции.",
        reply_markup=personal_office_keyboard()
    )

@router.message(F.text == "Мои задачи 📖")
async def personal_office(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    tasks = get_user_tasks(user_id)
    await message.answer(
        text=tasks
    )

@router.message(F.text == "Мои данные 📑")
async def my_data_executor(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = my_data(user_id)
    await message.answer(
        text=data,
        reply_markup=update_data()
    )

@router.message(F.text == "Поддержка 🤖")
async def my_data_executor(message: types.Message, state: FSMContext):
    await message.answer(
        text="Выберите нужную опцию",
        reply_markup=support()
    )

@router.message(F.text == "Основное меню")
async def basic_menu(message: types.Message, state: FSMContext):
    await message.answer(
        text="Основное меню.",
        reply_markup=get_executor_keyboard()
    )

@router.message(F.text == "Статистика заявок 📊")
async def statistics_of_applications(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    statistics = contractor_statistics(user_id)
    await message.answer(
        text=statistics,
        reply_markup=get_executor_keyboard()
    )

@router.message(F.text == "Как работать с заказами:")
async def my_data_executor(message: types.Message, state: FSMContext):
    await message.answer(
        text="""
        1. При появлении новой заявки вам придёт сообщение в чате.
        2. Выберите заявку, которую хотите исполнить. Нажмите "Взять задачу ➡️", укажите номер задачи.
        3. Информацию об актуальной заявке можно посмотреть в разделе "Мои задачи 📖".
        4. После завершения заказа любой исполнитель может нажать "Заявка выполнена ✅"
        5. 
        6. 
        7. 
        8. 
        """,
        reply_markup=get_executor_keyboard()
    )

@router.message(F.text == "Важные правила")
async def my_data_executor(message: types.Message, state: FSMContext):
    await message.answer(
        text="""
        Важные правила:
        • Время выполнения: Прибывайте на объект строго в указанное время. Если возникли задержки, сообщите клиенту и менеджеру.
        • Внешний вид: Необходим аккуратный внешний вид, будьте вежливы с клиентами.
        • Бережное отношение: Аккуратно обращайтесь с грузом, особенно с хрупкими предметами.
        • Отчетность: После завершения заказа обязательно обновите статус в боте.
        
        Спасибо за вашу работу! Чат-бот создан для того, 
        чтобы сделать ваш труд удобным и организованным. 
        Удачи в выполнении заказов! 💪
        """,
        reply_markup=get_executor_keyboard()
    )

@router.message(F.text == "Часто задаваемые вопросы")
async def my_data_executor(message: types.Message, state: FSMContext):
    await message.answer(
        text="""
        Часто задаваемые вопросы:

        1.⁠ ⁠ Где работа?
        Заявки отправляются в Telegram-канал по мере их поступления , Следите за уведомлениями.
        
        2.⁠ ⁠Как брать заявки?
        Если пришла заявка, то нажимайте кнопку «Еду 1». Тогда придет подтверждение, что вы закреплены за заявкой.
        
        3.⁠ Нас двое, трое, четверо и т. д. Как взять заявку на всех?
        Если вас много, то нажимайте кнопку "Едем в 2, 3, 4 и т.д." в соответствии с необходимым количеством.
        
        4.⁠ ⁠Не могу взять заявку. Что делать?
        Скорее всего заявка уже закрыта и мест нет. Либо на заявку могут поехать только самозанятые. Поэтому ждите когда освободятся места или получите статус самозанятого.
        
        5.⁠ ⁠Где контактный номер и кому звонить?
        Контактные данные вы получите после получения заявки. Функция "Мои заявки" отобразит вам контактный номер.
        
        6.⁠ ⁠Вопросы по оплате.
        Выплаты производим мы в день выполнения работ. Подробнее информация будет у менеджера.
        
        7.⁠ ⁠На сколько часов работы?
        Вся необходимая информация в заявке. Читайте внимательно.
        """,
        reply_markup=get_executor_keyboard()
    )