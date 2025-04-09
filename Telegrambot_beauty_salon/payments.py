from yookassa import Configuration, Payment
import os
from dotenv import load_dotenv

load_dotenv()

Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")


async def create_payment(amount, description, user_id, appointment_id):
    """
    Асинхронно создает платеж в платежной системе (например, YooKassa).

    Параметры:
    ----------
    amount : float | int
        Сумма платежа. Будет автоматически преобразована в строку.
    description : str
        Описание платежа (например, "Оплата записи на прием").
    user_id : int | str
        Идентификатор пользователя, который будет сохранен в метаданных платежа.
    appointment_id : int | str
        Идентификатор записи (на прием/услугу), который будет сохранен в метаданных платежа.

    Возвращает:
    -----------
    Payment
        Объект платежа, созданный в платежной системе.

    Пример использования:
    ---------------------
    ```python
    payment = await create_payment(
        amount=1000.50,
        description="Оплата консультации",
        user_id=123,
        appointment_id=456
    )
    ```

    Примечания:
    -----------
    - Платеж автоматически подтверждается (`capture=True`).
    - После оплаты пользователь будет перенаправлен в Telegram-бота (URL берется из `os.getenv('BOT_USERNAME')`).
    - Метаданные (`metadata`) включают `user_id` и `appointment_id` для связи платежа с пользователем и записью.
    - Валюта платежа фиксирована — RUB (рубли).
    """
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/{os.getenv('BOT_USERNAME')}"
        },
        "description": description,
        "metadata": {
            "user_id": user_id,
            "appointment_id": appointment_id
        },
        "capture": True  # Автоподтверждение платежа
    })
    return payment
