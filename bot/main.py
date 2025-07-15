from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

from bot.config import TOKEN
from bot.handlers import register_handlers

async def main():
    bot = Bot(token=TOKEN)
    bot.default_parse_mode = ParseMode.HTML

    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)

    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())