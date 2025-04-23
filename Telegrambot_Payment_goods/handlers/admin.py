from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
# from datetime import datetime

from states import OrderStates
from keyboards.admin_kb import get_admin_keyboard, get_update_choice_keyboard
from database import (
    create_service,
    get_service_by_id,
    update_service_description,
    update_service_amount,
    update_service,
    status_service
)

router = Router()

# СОЗДАТЬ ЗАКАЗ
@router.message(F.text == "Создать заказ")
async def create_order(message: types.Message, state: FSMContext):
    await message.answer("Опишите услугу:")
    await state.set_state(OrderStates.waiting_for_description)


@router.message(OrderStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите стоимость услуги:")
    await state.set_state(OrderStates.waiting_for_amount)


@router.message(OrderStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        description = data.get('description')

        service_id = create_service(description, amount)

        if service_id:
            await message.answer(
                f"Услуга создана!\nID услуги: {service_id}",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.answer(
                "Ошибка при создании услуги",
                reply_markup=get_admin_keyboard()
            )
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму:")
        return
    finally:
        await state.clear()

# ПРОСМОТР СТАТУСА
@router.message(F.text == "Посмотреть статус оплаты заказа")
async def check_order_status(message: types.Message, state: FSMContext):
    await message.answer("Введите № заказа:")
    await state.set_state(OrderStates.waiting_for_payment_status)


@router.message(OrderStates.waiting_for_payment_status)
async def process_admin_order_id(message: types.Message, state: FSMContext):
    order_id = message.text
    status = status_service(order_id)

    if status:
        await message.answer(
            f"Статус заказа {order_id}: {status}",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "Заказ не найден",
            reply_markup=get_admin_keyboard()
        )
    await state.clear()

# ИСПРАВЛЕНИЕ ЗАКАЗА
@router.message(F.text == "Исправить заказ")
async def update_order(message: types.Message, state: FSMContext):
    await message.answer("Введите № заказа для исправления:")
    await state.set_state(OrderStates.waiting_for_order_update)


@router.message(OrderStates.waiting_for_order_update)
async def process_order_update(message: types.Message, state: FSMContext):
    order_id = message.text
    service = get_service_by_id(order_id)

    if not service:
        await message.answer("Заказ не найден", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    await state.update_data(order_id=order_id)
    await message.answer(
        "Что вы хотите исправить?",
        reply_markup=get_update_choice_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_update_choice)


@router.message(OrderStates.waiting_for_update_choice)
async def process_update_choice(message: types.Message, state: FSMContext):
    choice = message.text
    data = await state.get_data()
    order_id = data.get('order_id')

    if choice == "Исправить описание":
        await message.answer("Введите новое описание:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(OrderStates.waiting_for_new_description)
    elif choice == "Исправить сумму":
        await message.answer("Введите новую сумму:", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(OrderStates.waiting_for_new_amount)
    elif choice == "Исправить описание и сумму":
        await message.answer("Введите новое описание:", reply_markup=types.ReplyKeyboardRemove())
        await state.update_data(update_both=True)
        await state.set_state(OrderStates.waiting_for_new_description)
    else:
        await message.answer("Неверный выбор", reply_markup=get_admin_keyboard())
        await state.clear()


@router.message(OrderStates.waiting_for_new_description)
async def process_new_description(message: types.Message, state: FSMContext):
    new_description = message.text
    data = await state.get_data()
    order_id = data.get('order_id')
    update_both = data.get('update_both', False)

    if update_both:
        await state.update_data(new_description=new_description)
        await message.answer("Теперь введите новую сумму:")
        await state.set_state(OrderStates.waiting_for_new_amount)
    else:
        if update_service_description(order_id, new_description):
            await message.answer(
                "Описание успешно обновлено!",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.answer(
                "Ошибка при обновлении описания",
                reply_markup=get_admin_keyboard()
            )
        await state.clear()


@router.message(OrderStates.waiting_for_new_amount)
async def process_new_amount(message: types.Message, state: FSMContext):
    try:
        new_amount = float(message.text)
        data = await state.get_data()
        order_id = data.get('order_id')
        new_description = data.get('new_description')

        if new_description:
            success = update_service(order_id, new_description, new_amount)
            msg = "Описание и сумма успешно обновлены!" if success else "Ошибка при обновлении"
        else:
            success = update_service_amount(order_id, new_amount)
            msg = "Сумма успешно обновлена!" if success else "Ошибка при обновлении суммы"

        await message.answer(msg, reply_markup=get_admin_keyboard())
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму:")
        return
    finally:
        await state.clear()

# ПРОСМОТР ЗАКАЗА
# ПРОСМОТР ЗАКАЗОВ
# изменить статус на сделано, увевдомление клиенту