from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime

from database import check_and_create_db, initialize_database, connect_to_database

load_dotenv()

# Инициализация бота с новым синтаксисом
bot = Bot(
    token=os.getenv('TELEGRAM_TOKEN_BOT'),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Проверка и создание базы данных, если она отсутствует
check_and_create_db()

# Инициализация базы данных (создание таблиц, если они отсутствуют)
initialize_database()

# Установление соединения с базой данных
cnx = connect_to_database()
if cnx:
    cursor = cnx.cursor()
    print("Подключение с бд успешно установлено.")
else:
    raise Exception("Не удалось установить соединение с базой данных")

ADMINS = list(map(int, os.getenv("ADMIN").split(',')))


class OrderStates(StatesGroup):
    waiting_for_order_id = State()
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_order_update = State()
    waiting_for_update_choice = State()
    waiting_for_new_description = State()
    waiting_for_new_amount = State()
    waiting_for_admin_order_id = State()


def get_user_keyboard(is_admin=False):
    if is_admin:
        buttons = [
            [KeyboardButton(text="Создать заказ")],
            [KeyboardButton(text="Посмотреть статус заказа")],
            [KeyboardButton(text="Исправить заказ")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="Оплатить услугу")],
            [KeyboardButton(text="Посмотреть статус услуги")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_payment_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Оплатить услугу", callback_data="pay_service")],
        [InlineKeyboardButton(text="Вернуться к выбору услуги", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_update_choice_keyboard():
    buttons = [
        [KeyboardButton(text="Исправить описание")],
        [KeyboardButton(text="Исправить сумму")],
        [KeyboardButton(text="Исправить описание и сумму")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_admin = message.from_user.id in ADMINS
    if is_admin:
        await message.answer("Добро пожаловать, Администратор", reply_markup=get_user_keyboard(is_admin=True))
    else:
        await message.answer("Приветствую вас в боте для оплаты услуг", reply_markup=get_user_keyboard())


@dp.message(F.text == "Оплатить услугу")
async def pay_service(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите № заказа который вам предоставил администратор бота. Введя № заказа, вы получите описание услуги и стоимость. В случае согласия, сможите ее оплатить")
    await state.set_state(OrderStates.waiting_for_order_id)


@dp.message(OrderStates.waiting_for_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
    order_id = message.text
    try:
        cursor.execute("SELECT description, Amount FROM My_services WHERE id_services = %s", (order_id,))
        service = cursor.fetchone()
        if service:
            description, amount = service
            await state.update_data(order_id=order_id, amount=amount)
            await message.answer(
                f"Описание услуги: {description}\nСтоимость: {amount} руб.",
                reply_markup=get_payment_keyboard()
            )
        else:
            await message.answer("Услуга не найдена", reply_markup=get_user_keyboard())
    except Exception as e:
        await message.answer("Произошла ошибка при поиске услуги")
        print(f"Error: {e}")
    await state.clear()


@dp.callback_query(F.data == "pay_service")
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    amount = data.get('amount')

    payment_token = os.getenv('PAYMENT_PROVIDER_TOKEN')
    if not payment_token:
        print("Отсутствует токен юКасса")
        await callback.message.answer("Что-то пошло не так. Обратитесь к администратору бота")
        return

    try:
        # Здесь должна быть реализация оплаты через ЮКассу
        # Пример:
        # await bot.send_invoice(...)

        # Обновляем статус заказа в базе данных
        cursor.execute(
            "UPDATE My_services SET payment_status = 'Оплачен', client = %s, paid_at = CURRENT_TIMESTAMP WHERE id_services = %s",
            (str(callback.from_user.id), order_id)  # Добавлена закрывающая скобка
        )
        cnx.commit()

        await callback.message.answer("Услуга успешно оплачена!", reply_markup=get_user_keyboard())
    except Exception as e:
        await callback.message.answer("Произошла ошибка при оплате")
        print(f"Error: {e}")
    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.answer("Вы вернулись в главное меню", reply_markup=get_user_keyboard())
    await callback.answer()


@dp.message(F.text == "Посмотреть статус услуги")
async def check_service_status(message: types.Message, state: FSMContext):
    await message.answer("Введите № заказа для проверки статуса:")
    await state.set_state(OrderStates.waiting_for_order_id)


@dp.message(F.text == "Создать заказ")
async def create_order(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("Опишите услугу")
        await state.set_state(OrderStates.waiting_for_description)


@dp.message(OrderStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите стоимость")
    await state.set_state(OrderStates.waiting_for_amount)


@dp.message(OrderStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        description = data.get('description')

        # Генерируем ID заказа
        order_id = int(datetime.now().timestamp())

        cursor.execute(
            "INSERT INTO My_services (id_services, description, Amount, payment_status, client) VALUES (%s, %s, %s, %s, %s)",
            (order_id, description, amount, 'Не оплачен', '')
        )
        cnx.commit()

        await message.answer(f"№ заказа: {order_id}", reply_markup=get_user_keyboard(is_admin=True))
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму")
        return
    except Exception as e:
        await message.answer("Произошла ошибка при создании заказа")
        print(f"Error: {e}")
    await state.clear()


@dp.message(F.text == "Посмотреть статус заказа")
async def check_order_status(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("Введите № заказа для проверки статуса:")
        await state.set_state(OrderStates.waiting_for_admin_order_id)


@dp.message(OrderStates.waiting_for_admin_order_id)
async def process_admin_order_id(message: types.Message, state: FSMContext):
    order_id = message.text
    try:
        cursor.execute("SELECT payment_status FROM My_services WHERE id_services = %s", (order_id,))
        status = cursor.fetchone()
        if status:
            await message.answer(f"Статус заказа: {status[0]}", reply_markup=get_user_keyboard(is_admin=True))
        else:
            await message.answer("Заказ не найден", reply_markup=get_user_keyboard(is_admin=True))
    except Exception as e:
        await message.answer("Произошла ошибка при проверке статуса")
        print(f"Error: {e}")
    await state.clear()


@dp.message(F.text == "Исправить заказ")
async def update_order(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer("Введите № заказа для исправления:")
        await state.set_state(OrderStates.waiting_for_order_update)


@dp.message(OrderStates.waiting_for_order_update)
async def process_order_update(message: types.Message, state: FSMContext):
    order_id = message.text
    try:
        cursor.execute("SELECT 1 FROM My_services WHERE id_services = %s", (order_id,))
        if not cursor.fetchone():
            await message.answer("Заказ не найден", reply_markup=get_user_keyboard(is_admin=True))
            await state.clear()
            return

        await state.update_data(order_id=order_id)
        await message.answer("Выберите что исправить:", reply_markup=get_update_choice_keyboard())
        await state.set_state(OrderStates.waiting_for_update_choice)
    except Exception as e:
        await message.answer("Произошла ошибка")
        print(f"Error: {e}")
        await state.clear()


@dp.message(OrderStates.waiting_for_update_choice)
async def process_update_choice(message: types.Message, state: FSMContext):
    choice = message.text
    data = await state.get_data()
    order_id = data.get('order_id')

    if choice == "Исправить описание":
        await message.answer("Введите новое описание:")
        await state.set_state(OrderStates.waiting_for_new_description)
    elif choice == "Исправить сумму":
        await message.answer("Введите новую сумму:")
        await state.set_state(OrderStates.waiting_for_new_amount)
    elif choice == "Исправить описание и сумму":
        await message.answer("Введите новое описание:")
        await state.set_state(OrderStates.waiting_for_new_description)
    else:
        await message.answer("Неверный выбор", reply_markup=get_user_keyboard(is_admin=True))
        await state.clear()


@dp.message(OrderStates.waiting_for_new_description)
async def process_new_description(message: types.Message, state: FSMContext):
    new_description = message.text
    data = await state.get_data()
    order_id = data.get('order_id')
    choice = data.get('choice', '')

    if choice == "Исправить описание и сумму":
        await state.update_data(new_description=new_description)
        await message.answer("Введите новую сумму:")
        await state.set_state(OrderStates.waiting_for_new_amount)
    else:
        try:
            cursor.execute(
                "UPDATE My_services SET description = %s WHERE id_services = %s",
                (new_description, order_id)
            )
            cnx.commit()
            await message.answer(f"Задача № {order_id} исправлена", reply_markup=get_user_keyboard(is_admin=True))
        except Exception as e:
            await message.answer("Произошла ошибка при обновлении описания")
            print(f"Error: {e}")
        await state.clear()


@dp.message(OrderStates.waiting_for_new_amount)
async def process_new_amount(message: types.Message, state: FSMContext):
    try:
        new_amount = float(message.text)
        data = await state.get_data()
        order_id = data.get('order_id')
        new_description = data.get('new_description')

        if new_description:
            cursor.execute(
                "UPDATE My_services SET description = %s, Amount = %s WHERE id_services = %s",
                (new_description, new_amount, order_id)
            )
        else:
            cursor.execute(
                "UPDATE My_services SET Amount = %s WHERE id_services = %s",
                (new_amount, order_id)
            )
        cnx.commit()
        await message.answer(f"Задача № {order_id} исправлена", reply_markup=get_user_keyboard(is_admin=True))
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму")
        return
    except Exception as e:
        await message.answer("Произошла ошибка при обновлении суммы")
        print(f"Error: {e}")
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())