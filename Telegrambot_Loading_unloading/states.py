from aiogram.fsm.state import State, StatesGroup

# ADMIN
# Ставим задачу
class OrderStates(StatesGroup):
    waiting_type_of_task = State()  # Тип задачи
    waiting_date_of_destination = State()  # Дата назначения
    waiting_appointment_time = State()  # Время назначения
    waiting_custom_time = State()  # Время вручную
    waiting_description = State()  # Описание
    waiting_main_address = State()   # Основной адрес
    waiting_additional_address = State()  # Дополнительный адрес
    waiting_required_workers = State()  # Количество человек
    waiting_worker_price = State()  # Цена

# РАБОТНИК
# Собираем данные
class UserRegistration(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    is_loader = State()
    is_driver = State()
    is_self_employed = State()
    inn = State()

# Берем задачу
class TaskNumber(StatesGroup):
    waiting_task_number = State()  # Ожидание номера задачи
