import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.config import BOT_TOKEN, ADMIN_ID
from bot.handlers import router
from bot.services import check_releases
from bot.storage import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)

        # Инициализация базы данных
        await init_db()

        # Настройка планировщика
        scheduler = AsyncIOScheduler()
        scheduler.add_job(check_releases, "interval", minutes=30, args=[bot], misfire_grace_time=60)
        scheduler.start()

        logger.info("Бот успешно запустился и работает нормально")

        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Бот упал: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())