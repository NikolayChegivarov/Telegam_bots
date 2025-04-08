from flask import Flask, request
from yookassa import Webhook
from bot_instance import bot
from handlers.payments_handlers import update_payment_status

app = Flask(__name__)


@app.route('/payment_webhook', methods=['POST'])
def webhook():
    """
    Обработчик webhook уведомлений от YooKassa о платежах.

    Этот эндпоинт принимает уведомления от YooKassa о состоянии платежей и
    выполняет соответствующие действия при успешном платеже.

    Args:
        request.json: JSON-тело запроса с данными уведомления YooKassa

    Returns:
        tuple: пустая строка и статус 200 OK

    Raises:
        ValueError: если не удалось распарсить данные webhook
        KeyError: если отсутствуют необходимые поля в метаданных платежа
        Exception: если произойдёт ошибка при обновлении статуса или отправке уведомления

    Пример JSON тела запроса:
    {
        "event": "payment.succeeded",
        "object": {
            "id": "21cfd974-000f-5000-8000-156d9e84c927",
            "amount": {
                "value": "100.00",
                "currency": "RUB"
            },
            "metadata": {
                "user_id": "12345"
            }
        }
    }

    Примечания:
        - Эндпоинт должен быть доступен извне для получения уведомлений от YooKassa
        - Все ошибки логируются и не влияют на возвращаемый статус
        - При успешном выполнении возвращается пустая строка со статусом 200
    """
    event = Webhook.parse(request.json)

    if event.event == 'payment.succeeded':
        payment = event.object
        user_id = payment.metadata['user_id']
        amount = payment.amount.value

        # Обновляем статус в БД
        update_payment_status(payment.id, 'paid')

        # Уведомляем пользователя в боте
        bot.send_message(
            chat_id=user_id,
            text=f"Оплата {amount} руб. подтверждена!"
        )

    return '', 200
