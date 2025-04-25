from aiogram import Router, types, F
from keyboards.executor_kb import get_executor_keyboard
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_executor_keyboard()
    )
    await callback.answer()