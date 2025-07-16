import aiohttp
import logging
from aiogram import Bot
from aiogram.types import BufferedInputFile
from bot.storage import get_all_apps, save_app
from bot.config import GITHUB_TOKEN
from bot.models import App
import io

logger = logging.getLogger(__name__)

async def get_latest_release(repo: str) -> dict:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 403:
                    logger.warning("Превышен лимит запросов к GitHub API")
                    return None
                else:
                    logger.error(f"Ошибка при получении релиза для {repo}: HTTP {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при запросе релиза для {repo}: {e}")
        return None

async def get_release_assets(repo: str) -> list:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=headers) as resp:
                if resp.status == 200:
                    release = await resp.json()
                    return [asset['name'] for asset in release['assets']]
                return []
    except Exception as e:
        logger.error(f"Ошибка при получении активов для {repo}: {e}")
        return []

async def check_releases(bot: Bot):
    try:
        apps = get_all_apps()
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        headers["Accept"] = "application/octet-stream"
        async with aiohttp.ClientSession() as session:
            for app in apps:
                release = await get_latest_release(app.repo)
                if not release or release['tag_name'] == app.latest_release:
                    continue
                app.latest_release = release['tag_name']
                save_app(app)
                release_notes = release.get('body', 'Описание релиза отсутствует.')
                for user_id in app.subscribers_users:
                    for asset in release['assets']:
                        if any(asset['name'].endswith(f.strip()) for f in app.asset_filters):
                            asset_url = asset['url']
                            logger.info(f"Загрузка файла для пользователя {user_id}: {asset_url} (имя: {asset['name']})")
                            try:
                                async with session.get(asset_url, headers=headers) as resp:
                                    if resp.status != 200:
                                        logger.error(f"Файл недоступен: {asset_url}, статус {resp.status}")
                                        continue
                                    file_data = await resp.read()
                                    await bot.send_document(
                                        chat_id=user_id,
                                        document=BufferedInputFile(file_data, filename=asset['name']),
                                        caption=f"Новый релиз для {app.title}: {release['name']}\n{release_notes}"
                                    )
                                    logger.info(f"Отправлен релиз {app.title} пользователю {user_id}")
                            except Exception as e:
                                logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
                for chat_id in app.subscribers_chats:
                    for asset in release['assets']:
                        if any(asset['name'].endswith(f.strip()) for f in app.asset_filters):
                            asset_url = asset['url']
                            logger.info(f"Загрузка файла для чата {chat_id}: {asset_url} (имя: {asset['name']})")
                            try:
                                async with session.get(asset_url, headers=headers) as resp:
                                    if resp.status != 200:
                                        logger.error(f"Файл недоступен: {asset_url}, статус {resp.status}")
                                        continue
                                    file_data = await resp.read()
                                    await bot.send_document(
                                        chat_id=chat_id,
                                        document=BufferedInputFile(file_data, filename=asset['name']),
                                        caption=f"Новый релиз для {app.title}: {release['name']}\n{release_notes}"
                                    )
                                    logger.info(f"Отправлен релиз {app.title} в чат {chat_id}")
                            except Exception as e:
                                logger.error(f"Ошибка отправки в чат {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка в check_releases: {e}")