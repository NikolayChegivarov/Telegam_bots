from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database import update_payment_status
import aiohttp
from aiogram import Bot
from typing import Optional, Dict, Any
from keyboards.client_kb import get_client_keyboard
from config import Config

router = Router()

@router.callback_query(F.data == "pay_service")
async def process_payment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    id_services = data.get('id_services')
    description = data.get('description')
    amount = data.get('amount')
    user_id = data.get('user_id')

    print(f"ПОЛУЧИЛИ ДАННЫЕ?: id_services {id_services} description {description} amount {amount}")

    if not id_services or not amount:
        await callback.message.answer("Ошибка: данные заказа не найдены, обратитесь к администратору.")
        await state.clear()
        return

    try:
        # Создаем платеж в ЮKassa
        payment = await create_yookassa_payment(
            bot=bot,
            user_id=user_id,
            amount=amount,
            description=description,
            shop_id=Config.SHOP_ID,
            secret_key=Config.PAYMENT_PROVIDER_TOKEN
        )

        # Получаем URL для оплаты
        confirmation_url = payment.get('confirmation', {}).get('confirmation_url')
        if confirmation_url:
            await callback.message.answer(
                f"Для оплаты перейдите по ссылке: {confirmation_url}\n"
                "После успешной оплаты вы получите уведомление.",
                reply_markup=get_client_keyboard()
            )
        else:
            await callback.message.answer("Ошибка при создании платежа")

    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {str(e)}")
        print(f"Произошла ошибка: {str(e)}")

    await callback.answer()

async def create_yookassa_payment(
        bot: Bot,
        user_id: int,
        amount: float,
        description: str,
        shop_id: str,
        secret_key: str,
        return_url: Optional[str] = None,
        currency: str = "RUB",
        save_payment_method: bool = False,
        metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Создает платеж через ЮKassa API
    """
    # Получаем информацию о боте, чтобы узнать username
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    url = "https://api.yookassa.ru/v3/payments"

    headers = {
        "Idempotence-Key": str(user_id),
        "Content-Type": "application/json",
    }

    auth = aiohttp.BasicAuth(shop_id, secret_key)

    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": currency
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": return_url or f"https://t.me/{bot_username}?start=payment_{user_id}"
        },
        "description": description,
        "save_payment_method": save_payment_method,
        "metadata": metadata or {"user_id": user_id, "telegram_username": bot_username}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, auth=auth) as response:
            response_data = await response.json()
            if response.status != 200:
                error_description = response_data.get('description', 'Unknown error')
                raise Exception(f"YooKassa API error: {error_description}")
            return response_data