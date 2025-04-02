from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from database import connect_to_database


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # Пропускаем команду /start и /help
        if event.text in ['/start', '/help']:
            return await handler(event, data)

        conn = connect_to_database()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE id_user_telegram = %s", (event.from_user.id,))
                if not cursor.fetchone():
                    await event.answer("Пожалуйста, сначала запустите бота с помощью команды /start")
                    return
        finally:
            conn.close()

        return await handler(event, data)