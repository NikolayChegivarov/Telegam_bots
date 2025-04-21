from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_for_order_id = State()
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_order_update = State()
    waiting_for_update_choice = State()
    waiting_for_new_description = State()
    waiting_for_new_amount = State()
    waiting_for_admin_order_id = State()
