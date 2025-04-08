# Здесь расположены дополнительные функции.
from database import connect_to_database
from typing import Optional, Dict, Any


async def get_user_role(user_id: int) -> Optional[str]:
    """Получить роль пользователя (client/master/admin)"""
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.type_user FROM users u
                JOIN type t ON u.id_user_type = t.id_user_type
                WHERE u.id_user_telegram = %s
            """, (user_id,))
            result = cursor.fetchone()
            print(f"Результат:   {result[0]}")
            return result[0] if result else None
    finally:
        conn.close()


async def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    role = await get_user_role(user_id)
    return role == 'ADMIN'


async def is_client(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    role = await get_user_role(user_id)
    return role == 'CLIENT'


async def format_service_info(service_data: Dict[str, Any]) -> str:
    """Форматировать информацию об услуге для вывода"""
    return (
        f"<b>{service_data['name']}</b>\n"
        f"💰 Цена: {service_data['price']} руб.\n"
        f"⏱ Длительность: {service_data['duration']} мин.\n"
        f"📝 Описание: {service_data.get('description', 'нет описания')}"
    )


async def notify_master_about_appointment(bot, master_id: int, client_name: str, service_name: str, date: str, time: str):
    """Уведомить мастера о новой записи"""
    try:
        await bot.send_message(
            master_id,
            f"📌 Новая запись!\n\n"
            f"👤 Клиент: {client_name}\n"
            f"💇 Услуга: {service_name}\n"
            f"📅 Дата: {date}\n"
            f"⏰ Время: {time}"
        )
    except Exception as e:
        print(f"Ошибка при уведомлении мастера: {e}")
