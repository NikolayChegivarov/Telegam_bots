from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.generate import ai_generate

router = Router()


class Gen(StatesGroup):
    """
    Gen - имя группы состояний
    StatesGroup - базовый класс из aiogram, который позволяет создавать группы состояний
    wait = State() - определяет конкретное состояние внутри группы
    """
    wait = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать. Напишите свой запрос.")


@router.message(Gen.wait)
async def stop_flood(message: Message):
    await message.answer("Подождите ваш запрос генерируется")


@router.message()
async def generating(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)  # Установка состояния ожидания.
    response = await ai_generate(message.text)  # Генерация ответа.
    await message.answer(response)  # Отправка результата.
    await state.clear()  # Очистка состояния.
