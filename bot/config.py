import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Опционально: токен GitHub для увеличения лимитов API
DB_PATH = "bot_data.db"

print(os.getenv("GITHUB_TOKEN"))

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN должен быть указан в файле .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID должен быть указан в файле .env")