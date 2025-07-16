import aiohttp
import logging
from aiogram import Bot
from aiogram.types import BufferedInputFile
from bot.storage import get_all_apps, save_app
from bot.config import GITHUB_TOKEN
from bot.models import App
import fnmatch

logger = logging.getLogger(__name__)

async def get_latest_release(repo: str) -> dict:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    headers["Accept"] = "application/vnd.github+json"
    headers["X-GitHub-Api-Version"] = "2022-11-28"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    logger.error(f"Ошибка авторизации для {repo}: HTTP 401 - Неверный токен")
                    return None
                elif resp.status == 403:
                    logger.warning(f"Превышен лимит запросов к GitHub API для {repo}")
                    return None
                else:
                    logger.error(f"Ошибка при получении релиза для {repo}: HTTP {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при запросе релиза для {repo}: {e}")
        return None

async def get_release_assets(repo: str) -> list:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    headers["Accept"] = "application/vnd.github+json"
    headers["X-GitHub-Api-Version"] = "2022-11-28"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/repos/{repo}/releases/latest", headers=headers) as resp:
                if resp.status == 200:
                    release = await resp.json()
                    return [asset['name'] for asset in release['assets']]
                elif resp.status == 401:
                    logger.error(f"Ошибка авторизации для активов {repo}: HTTP 401 - Неверный токен")
                    return []
                return []
    except Exception as e:
        logger.error(f"Ошибка при получении активов для {repo}: {e}")
        return []

async def check_releases(bot: Bot):
    try:
        apps = get_all_apps()
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        async with aiohttp.ClientSession() as session:
            for app in apps:
                if not app.asset_filters:
                    logger.warning(f"Фильтры для {app.key} не указаны, пропускаем проверку обновлений")
                    continue
                release = await get_latest_release(app.repo)
                if not release or release['tag_name'] == app.latest_release:
                    continue
                app.latest_release = release['tag_name']
                save_app(app)
                release_notes = release.get('body', 'Описание релиза отсутствует.')
                caption = f"Новый релиз для {app.title}: {release['name']}\n{release_notes}"
                for user_id in app.subscribers_users:
                    sent = False
                    for asset in release['assets']:
                        if any(fnmatch.fnmatch(asset['name'], f.strip()) for f in app.asset_filters):
                            asset_url = asset['browser_download_url']
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
                                        caption=caption if not sent else None
                                    )
                                    sent = True
                                    logger.info(f"Отправлен файл {asset['name']} для {app.title} пользователю {user_id}")
                            except Exception as e:
                                logger.error(f"Ошибка загрузки файла {asset['name']} для пользователя {user_id}: {e}")
                for chat_id in app.subscribers_chats:
                    sent = False
                    for asset in release['assets']:
                        if any(fnmatch.fnmatch(asset['name'], f.strip()) for f in app.asset_filters):
                            asset_url = asset['browser_download_url']
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
                                        caption=caption if not sent else None
                                    )
                                    sent = True
                                    logger.info(f"Отправлен файл {asset['name']} для {app.title} в чат {chat_id}")
                            except Exception as e:
                                logger.error(f"Ошибка загрузки файла {asset['name']} для чата {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка в check_releases: {e}")