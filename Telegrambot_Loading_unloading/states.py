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
    waiting_task_number_add = State()  # Ожидание номера задачи, что бы взять задачу
    waiting_task_number_dell = State()  # Ожидание номера задачи, что бы отказаться от задачи
    waiting_task_number_report = State()  # Ожидание номера задачи, что бы отчитаться о выполнении
    waiting_task_number_complete = State()  # Ожидание номера задачи, что бы завершить
    waiting_task_number_delete = State()  # Ожидание номера задачи, что удалить задачу

# ID user
class IdUser(StatesGroup):
    waiting_user_number = State()  # Ожидание номера пользователя для просмотра анкеты
    waiting_contractor_statistics = State()  # Ожидание номера пользователя для статистики
    waiting_contractor_dell = State()  # Ожидание номера пользователя для удаления

class Text(StatesGroup):
    waiting_contractor_commentary = State()  # Ожидание номера пользователя комментария
    waiting_contractor_commentary2 = State()  # Ожидание комментария

