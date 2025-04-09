from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot(os.getenv('TELEGRAM_TOKEN_BOT'), parse_mode=ParseMode.HTML)
dp = Dispatcher()


@dp.message(commands=['start'])
async def start(message: types.Message):
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title='Название товара или услуги',
        description='Описание товара или услуги',
        payload='invoice',
        provider_token=os.getenv('YOOKASSA_SECRET_KEY'),
        currency='USD',
        prices=[types.LabeledPrice(label='Описание конкретной позиции', amount=5 * 100)]  # 5 USD в центах
    )


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
