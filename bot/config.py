import os
from dotenv import load_dotenv

# Путь к базе данных SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")

def reload_env():
    """Перезагружает переменные окружения из .env файла."""
    load_dotenv(override=True)
    return {
        "BOT_TOKEN": os.getenv("BOT_TOKEN"),
        "ADMIN_ID": int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None,
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")
    }

# Загрузка переменных при старте
env_vars = reload_env()
BOT_TOKEN = env_vars["BOT_TOKEN"]
ADMIN_ID = env_vars["ADMIN_ID"]
GITHUB_TOKEN = env_vars["GITHUB_TOKEN"]