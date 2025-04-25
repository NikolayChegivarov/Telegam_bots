from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import OrderStates

router = Router()


# СОЗДАТЬ ЗАКАЗ
@router.message(F.text == "Поставить задачу 📝")
async def create_order(message: types.Message, state: FSMContext):
    await message.answer("Выбери тип задачи:")
    await state.set_state(OrderStates.waiting_type_of_task)

@router.message(OrderStates.waiting_type_of_task)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(type_of_task=message.text)
    await message.answer("Введите дату назначения:")
    await state.set_state(OrderStates.waiting_date_of_destination)

@router.message(OrderStates.waiting_date_of_destination)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(date_of_destination=message.text)
    await message.answer("Введите время назначения:")
    await state.set_state(OrderStates.waiting_appointment_time)

@router.message(OrderStates.waiting_appointment_time)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(appointment_time=message.text)
    await message.answer("Введите описание задачи:")
    await state.set_state(OrderStates.waiting_description)

@router.message(OrderStates.waiting_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Адрес основной:")
    await state.set_state(OrderStates.waiting_main_address)

@router.message(OrderStates.waiting_main_address)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(main_address=message.text)
    await message.answer("Адрес дополнительный:")
    await state.set_state(OrderStates.waiting_additional_address)

@router.message(OrderStates.waiting_additional_address)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(additional_address=message.text)
    await message.answer("Укажите необходимое количество человек.")
    await state.set_state(OrderStates.waiting_required_workers)

@router.message(OrderStates.waiting_required_workers)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(required_workers=message.text)
    await message.answer("Задача сохранена и отправлена исполнителям.")


