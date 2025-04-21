from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from states import OrderStates
from keyboards.client_kb import get_client_keyboard, get_payment_keyboard
from database import get_service_by_id, status_service

router = Router()


@router.message(F.text == "Оплатить услугу")
async def pay_service(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите ID заказа, который вам предоставил администратор:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderStates.waiting_for_order_id)


@router.message(OrderStates.waiting_for_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
    order_id = message.text
    service = get_service_by_id(order_id)

    if service:
        description, amount = service[1], service[2]  # description и amount из БД
        await state.update_data(order_id=order_id, amount=amount)
        await message.answer(
            f"Описание услуги: {description}\nСтоимость: {amount} руб.",
            reply_markup=get_payment_keyboard()
        )
    else:
        await message.answer(
            "Услуга не найдена. Проверьте ID заказа.",
            reply_markup=get_client_keyboard()
        )
    await state.clear()


@router.message(F.text == "Посмотреть статус услуги")
async def check_service_status(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите ID заказа для проверки статуса:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderStates.waiting_for_order_id)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_client_keyboard()
    )
    await callback.answer()