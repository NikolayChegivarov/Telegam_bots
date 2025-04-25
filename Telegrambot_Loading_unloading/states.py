from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    # ADMIN
    waiting_type_of_task = State()  # Тип задачи
    waiting_date_of_destination = State()  # Дата назначения
    waiting_appointment_time = State()  # Время назначения
    waiting_description = State()  # Описание
    waiting_main_address = State()   # Основной адрес
    waiting_additional_address = State()  # Дополнительный адрес
    waiting_required_workers = State()  # Количество человек

    waiting_for_new_amount = State()  # Ожидание новой стоимости
    waiting_for_payment_status = State()  # Ожидание статуса оплаты
    waiting_for_status_order_id = State()   # Состояние ожидания № заказа для получения статуса