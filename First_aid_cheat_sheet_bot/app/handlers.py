from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Это телеграм бот предназначен для тех кто уже прошел курсы "
                         "по оказанию первой медицинской помощи. Предназначен исключительно "
                         "для повторения алгоритма действий усвоенных на практике..")
