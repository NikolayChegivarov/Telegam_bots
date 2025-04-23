from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_for_order_id = State()  # Выбора услуги для оплаты
    waiting_for_description = State()  # Ожидание описания услуги
    waiting_for_amount = State()  # Ожидание стоимости услуги
    waiting_for_order_update = State()   # Ожидание № заказа для исправления
    waiting_for_update_choice = State()  # Ожидание выбора исправления
    waiting_for_new_description = State()  # Ожидание нового описания
    waiting_for_new_amount = State()  # Ожидание новой стоимости
    waiting_for_payment_status = State()  # Ожидание статуса оплаты
    waiting_for_status_order_id = State()   # Состояние ожидания № заказа для получения статуса
