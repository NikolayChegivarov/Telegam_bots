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

    print(f"id_services {id_services} description {description} amount {amount}")

    if not id_services or not amount:
        await callback.message.answer("Ошибка: данные заказа не найдены")
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

    await callback.answer()

async def create_yookassa_payment(
        bot: Bot,  # Changed from types.Bot to Bot since you're importing Bot directly
        user_id: int,  # ID пользователя в Telegram
        amount: float,  # Сумма платежа
        description: str,  # Описание платежа
        shop_id: str,  # ID магазина в ЮKassa
        secret_key: str,  # Секретный ключ ЮKassa
        return_url: Optional[str] = None,  # URL для возврата после оплаты (опционально)
        currency: str = "RUB",  # Валюта платежа (по умолчанию RUB)
        save_payment_method: bool = False,  # Сохранить метод оплаты (по умолчанию False)
        metadata: Optional[Dict[str, Any]] = None  # Дополнительные метаданные (опционально)
) -> Dict[str, Any]:
    """
    Создает платеж через ЮKassa API
    """
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
            "return_url": return_url or f"https://t.me/{bot.username}?start=payment_{user_id}"
        },
        "description": description,
        "save_payment_method": save_payment_method,
        "metadata": metadata or {"user_id": user_id, "telegram_username": bot.username}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, auth=auth) as response:
            response_data = await response.json()
            if response.status != 200:
                error_description = response_data.get('description', 'Unknown error')
                raise Exception(f"YooKassa API error: {error_description}")
            return response_data