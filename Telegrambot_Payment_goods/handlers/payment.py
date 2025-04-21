from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from keyboards.payment_kb import get_payment_keyboard
from keyboards.client_kb import get_client_keyboard
from database import update_payment_status

router = Router()

@router.callback_query(F.data == "pay_service")
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    amount = data.get('amount')

    # Здесь должна быть реализация оплаты через ЮКассу
    # await bot.send_invoice(...)

    if update_payment_status(order_id, str(callback.from_user.id)):
        await callback.message.answer("Услуга успешно оплачена!",
                                    reply_markup=get_client_keyboard())
    else:
        await callback.message.answer("Произошла ошибка при оплате")
    await callback.answer()