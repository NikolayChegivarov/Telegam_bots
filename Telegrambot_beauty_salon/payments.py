from yookassa import Configuration, Payment
import os
from dotenv import load_dotenv

load_dotenv()

Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")


async def create_payment(amount, description, user_id, appointment_id):
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