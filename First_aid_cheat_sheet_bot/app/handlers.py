from aiogram import F, Router
from aiogram.types import Message, CallbackQuery  # Добавлен импорт CallbackQuery
from aiogram.filters import CommandStart
from app.keyboards import *

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Это телеграм бот предназначен для тех кто уже прошел курсы "
        "по оказанию первой медицинской помощи. Предназначен исключительно "
        "для повторения алгоритма действий усвоенных на практике.",
        reply_markup=get_start_inline_keyboard()
    )
    print("\nПреветственное сообщение.")


@router.callback_query(F.data == "start")
async def start_button_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    *ОЦЕНКА СИТУАЦИИ И БЕЗОПАСНОСТЬ*

    При обнаружении в поле зрения пострадавших, необходимо:
    - Остановиться.
    - Если вы не одни, громко и четко подать сигнал группе: *"Стоп! Опасность!"*
    - Оценить обстановку вокруг.
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=danger_testing()
    )


@router.callback_query(F.data == "danger")  # Оцениваем опасность.
async def danger(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    1. Определить угрозы для себя и пострадавшего. 
    2. Обеспечить безопасность места происшествия. 
    3. При необходимости извлечь пострадавшего из опасной зоны.
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=security()
    )


@router.callback_query(F.data == "no_danger")  # Если нет опасности.
async def consciousness(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    Выясняем в сознании ли пострадавший, окликнув его голосом или постучав слегка по плечам. 
    Если человек не реагирует на вас, значит он без сознания. 
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=consciousness_testing()
    )


@router.callback_query(F.data == "in_consciousness")  # Если в сознании.
async def bleeding(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    Есть кровотечения?
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=bleeding_testing()
    )


@router.callback_query(F.data == "is_bleeding")  # Есть кровотечение.
async def what_a_bleeding(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    Кровотечение интенсивное?
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=intensive_testing()
    )


@router.callback_query(F.data == "intensive")  # Интенсивное кровотечение.
async def what_a_bleeding(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    Основная опасность - кровопотеря. Сразу используем прямое давление. 
    То есть необходимо зажать рану, можно силами пострадавшего. 
    Получается остановить кровь?
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=intensive_testing()
    )


@router.callback_query(F.data == "it_worked")  # Получается остановить кровь.
async def what_a_bleeding(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    Накладываем давящую повязку. Помогло?
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=intensive_testing()
    )

@router.callback_query(F.data == "in_consciousness")  #
async def bleeding(callback_query: CallbackQuery):
    await callback_query.answer()
    text = """
    Вызываем скорую помощь. Сообщаем что случилось, количество пострадавших, состояние пострадавших.
    """
    await callback_query.message.answer(
        text,
        parse_mode="Markdown",
    )

