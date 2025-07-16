import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramUnauthorizedError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.config import BOT_TOKEN
from bot.handlers import router
from bot.services import check_releases

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    try:
        bot = Bot(token=BOT_TOKEN)
    except TelegramUnauthorizedError as e:
        logger.error(f"Ошибка: Неверный токен Telegram-бота: {e}")
        return
    except Exception as e:
        logger.error(f"Ошибка при инициализации бота: {e}")
        return

    try:
        dp = Dispatcher()
        dp.include_router(router)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(check_releases, 'interval', minutes=30, args=[bot])
        scheduler.start()
        logger.info("Бот успешно запустился и работает нормально")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())