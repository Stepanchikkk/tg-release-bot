from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.storage import get_all_apps, get_app, save_app, delete_app
from bot.models import App
from bot.config import ADMIN_ID, GITHUB_TOKEN
from bot.services import get_latest_release, get_release_assets, check_releases
from bot.utils import validate_repo, validate_key
import logging
import aiohttp
import io

logger = logging.getLogger(__name__)

router = Router()

class AddAppStates(StatesGroup):
    key = State()
    title = State()
    link = State()
    repo = State()
    asset_filters = State()
    select_assets = State()

def get_main_menu(apps):
    buttons = [[InlineKeyboardButton(text=app.title, callback_data=f"app:{app.key}")] for app in apps]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_app_menu(app: App, is_subscribed: bool, is_admin: bool = False):
    buttons = [
        [InlineKeyboardButton(text="📦 Скачать", callback_data=f"download:{app.key}")],
        [InlineKeyboardButton(text="🌐 Ссылка", callback_data=f"link:{app.key}")],
        [InlineKeyboardButton(text="🔔 Подписаться" if not is_subscribed else "🔕 Отписаться", callback_data=f"subscribe:{app.key}")]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete:{app.key}")])
        buttons.append([InlineKeyboardButton(text="🔄 Установить репозиторий", callback_data=f"setrepo:{app.key}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_asset_selection_menu(assets: list, selected: list):
    buttons = [
        [InlineKeyboardButton(
            text=f"{'✅ ' if assets[i] in selected else ''}{assets[i]}",
            callback_data=f"asset:{i}"
        )] for i in range(len(assets))
    ]
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="asset_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def start(message: Message):
    try:
        apps = get_all_apps()
        welcome_text = (
            "Добро пожаловать! Это бот для отслеживания релизов приложений на GitHub.\n\n"
            "Доступные команды:\n"
            "/start - Показать это сообщение\n"
            "/menu - Открыть меню приложений\n"
            "/help - Показать справку по командам"
        )
        if not apps:
            await message.answer(f"{welcome_text}\n\nПока нет доступных приложений.")
            return
        await message.answer(f"{welcome_text}\n\nВыберите приложение:", reply_markup=get_main_menu(apps))
        logger.info(f"Пользователь {message.from_user.id} запустил бот")
    except Exception as e:
        logger.error(f"Ошибка в команде start: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command("menu"))
async def menu(message: Message):
    try:
        apps = get_all_apps()
        if not apps:
            await message.answer("Пока нет доступных приложений.")
            return
        await message.answer("Выберите приложение:", reply_markup=get_main_menu(apps))
        logger.info(f"Пользователь {message.from_user.id} открыл меню")
    except Exception as e:
        logger.error(f"Ошибка в команде menu: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command("help"))
async def help_command(message: Message):
    try:
        help_text = (
            "📋 **Команды для всех пользователей**:\n"
            "/start - Запустить бот и показать приветственное сообщение\n"
            "/menu - Показать меню приложений\n"
            "/help - Показать эту справку"
        )
        await message.answer(help_text, parse_mode="Markdown")
        logger.info(f"Пользователь {message.from_user.id} запросил справку")
    except Exception as e:
        logger.error(f"Ошибка в команде help: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command("adminhelp"))
async def admin_help_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только глобальному администратору.")
        return
    try:
        help_text = (
            "🔐 **Команды для администратора**:\n"
            "/addapp - Начать добавление нового приложения\n"
            "/removeapp <key> - Удалить приложение по ключу\n"
            "/setrepo <key> <owner/repo> - Установить GitHub-репозиторий для приложения\n"
            "/apps - Показать список всех приложений\n"
            "/checkupdates - Ручная проверка обновлений"
        )
        await message.answer(help_text, parse_mode="Markdown")
        logger.info(f"Админ {message.from_user.id} запросил справку по админским командам")
    except Exception as e:
        logger.error(f"Ошибка в команде adminhelp: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(Command("addapp"))
async def add_app(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Только глобальный администратор может добавлять приложения.")
        return
    await message.answer("Введите ключ приложения (уникальный идентификатор, например, 'lsposed'):")
    await state.set_state(AddAppStates.key)
    logger.info(f"Админ {message.from_user.id} начал добавление приложения")

@router.message(AddAppStates.key)
async def process_key(message: Message, state: FSMContext):
    key = message.text.strip()
    if not validate_key(key):
        await message.answer("Недопустимый ключ. Используйте только буквы, цифры и подчеркивания.")
        return
    if get_app(key):
        await message.answer("Приложение с таким ключом уже существует.")
        return
    await state.update_data(key=key)
    await message.answer("Введите название приложения (например, 'LSPosed'):")
    await state.set_state(AddAppStates.title)
    logger.info(f"Админ {message.from_user.id} указал ключ: {key}")

@router.message(AddAppStates.title)
async def process_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(title=title)
    await message.answer("Введите ссылку на приложение (например, 'https://github.com/LSPosed/LSPosed'):")
    await state.set_state(AddAppStates.link)
    logger.info(f"Админ {message.from_user.id} указал название: {title}")

@router.message(AddAppStates.link)
async def process_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if not link.startswith("http"):
        await message.answer("Недопустимая ссылка. Должна начинаться с http:// или https://")
        return
    await state.update_data(link=link)
    await message.answer("Введите GitHub-репозиторий (формат: owner/repo, например, 'LSPosed/LSPosed'):")
    await state.set_state(AddAppStates.repo)
    logger.info(f"Админ {message.from_user.id} указал ссылку: {link}")

@router.message(AddAppStates.repo)
async def process_repo(message: Message, state: FSMContext):
    repo = message.text.strip()
    if not validate_repo(repo):
        await message.answer("Недопустимый формат репозитория. Используйте формат 'owner/repo' (например, 'LSPosed/LSPosed').")
        return
    release = await get_latest_release(repo)
    if not release:
        await message.answer("Не удалось получить репозиторий. Убедитесь, что он существует и доступен.")
        return
    await state.update_data(repo=repo)
    assets = await get_release_assets(repo)
    if not assets:
        await message.answer("В последнем релизе нет активов. Введите фильтры для файлов вручную (через запятую, например, '*.apk,*.zip'):")
        await state.set_state(AddAppStates.asset_filters)
    else:
        await state.update_data(available_assets=assets, selected_asset_indices=[])
        await message.answer("Выберите файлы для включения:", reply_markup=get_asset_selection_menu(assets, []))
        await state.set_state(AddAppStates.select_assets)
    logger.info(f"Админ {message.from_user.id} указал репозиторий: {repo}")

@router.callback_query(AddAppStates.select_assets, F.data.startswith("asset:"))
async def select_asset(callback: CallbackQuery, state: FSMContext):
    try:
        asset_index = int(callback.data.split(":", 1)[1])
        data = await state.get_data()
        assets = data.get("available_assets", [])
        selected_indices = data.get("selected_asset_indices", [])
        if asset_index in selected_indices:
            selected_indices.remove(asset_index)
        else:
            selected_indices.append(asset_index)
        await state.update_data(selected_asset_indices=selected_indices)
        selected_assets = [assets[i] for i in selected_indices]
        await callback.message.edit_reply_markup(
            reply_markup=get_asset_selection_menu(assets, selected_assets)
        )
        logger.info(f"Админ {callback.from_user.id} выбрал/снял актив с индексом: {asset_index}")
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка при выборе актива: {e}")
        await callback.message.edit_text("Произошла ошибка при выборе файла.")

@router.callback_query(AddAppStates.select_assets, F.data == "asset_done")
async def finish_assets(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assets = data.get("available_assets", [])
    selected_indices = data.get("selected_asset_indices", [])
    if not selected_indices:
        await callback.message.edit_text("Файлы не выбраны. Введите фильтры для файлов вручную (через запятую, например, '*.apk,*.zip'):")
        await state.set_state(AddAppStates.asset_filters)
        return
    selected_assets = [assets[i] for i in selected_indices]
    await state.update_data(asset_filters=selected_assets)
    app = App(
        key=data["key"],
        title=data["title"],
        link=data["link"],
        repo=data["repo"],
        asset_filters=selected_assets,
        subscribers_users=[],
        subscribers_chats=[],
        latest_release=None
    )
    save_app(app)
    await callback.message.edit_text(f"Приложение {app.title} успешно добавлено!")
    apps = get_all_apps()
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu(apps))
    await state.clear()
    logger.info(f"Админ {callback.from_user.id} добавил приложение: {app.key}")

@router.message(AddAppStates.asset_filters)
async def process_filters(message: Message, state: FSMContext):
    filters = [f.strip() for f in message.text.split(",") if f.strip()]
    if not filters:
        await message.answer("Требуется хотя бы один фильтр.")
        return
    data = await state.get_data()
    app = App(
        key=data["key"],
        title=data["title"],
        link=data["link"],
        repo=data["repo"],
        asset_filters=filters,
        subscribers_users=[],
        subscribers_chats=[],
        latest_release=None
    )
    save_app(app)
    await message.answer(f"Приложение {app.title} успешно добавлено!")
    apps = get_all_apps()
    await message.answer("Главное меню:", reply_markup=get_main_menu(apps))
    await state.clear()
    logger.info(f"Админ {message.from_user.id} добавил приложение: {app.key}")

@router.message(Command("removeapp"))
async def remove_app(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Только глобальный администратор может удалять приложения.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.answer("Использование: /removeapp <ключ>")
        return
    key = args[1].strip()
    if get_app(key):
        delete_app(key)
        await message.answer(f"Приложение {key} удалено!")
        apps = get_all_apps()
        await message.answer("Главное меню:", reply_markup=get_main_menu(apps))
        logger.info(f"Админ {message.from_user.id} удалил приложение: {key}")
    else:
        await message.answer("Приложение не найдено.")

@router.message(Command("setrepo"))
async def set_repo(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Только глобальный администратор может устанавливать репозитории.")
        return
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.answer("Использование: /setrepo <ключ> <owner/repo>")
        return
    key, repo = args[1].strip(), args[2].strip()
    if not validate_repo(repo):
        await message.answer("Недопустимый формат репозитория. Используйте 'owner/repo' (например, 'LSPosed/LSPosed').")
        return
    app = get_app(key)
    if not app:
        await message.answer("Приложение не найдено.")
        return
    release = await get_latest_release(repo)
    if not release:
        await message.answer("Не удалось получить репозиторий. Убедитесь, что он существует и доступен.")
        return
    app.repo = repo
    save_app(app)
    await message.answer(f"Репозиторий для {key} обновлён на {repo}!")
    logger.info(f"Админ {message.from_user.id} установил репозиторий для {key}: {repo}")

@router.message(Command("apps"))
async def list_apps(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Только глобальный администратор может просматривать список приложений.")
        return
    apps = get_all_apps()
    if not apps:
        await message.answer("Нет доступных приложений.")
        return
    text = "Приложения:\n" + "\n".join(
        f"{app.title} ({app.key})\n  Репозиторий: {app.repo}\n  Подписчики: {len(app.subscribers_users)} пользователей, {len(app.subscribers_chats)} чатов\n  Фильтры: {', '.join(app.asset_filters)}"
        for app in apps
    )
    await message.answer(text)
    logger.info(f"Админ {message.from_user.id} запросил список приложений")

@router.message(Command("checkupdates"))
async def check_updates(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Только глобальный администратор может проверять обновления.")
        return
    await message.answer("Проверка обновлений...")
    await check_releases(bot)
    await message.answer("Проверка обновлений завершена!")
    logger.info(f"Админ {message.from_user.id} запустил ручную проверку обновлений")

@router.callback_query(F.data.startswith("app:"))
async def app_selected(callback: CallbackQuery):
    try:
        key = callback.data.split(":", 1)[1]
        app = get_app(key)
        if not app:
            await callback.message.edit_text("Приложение не найдено.")
            return
        is_subscribed = (
            callback.from_user.id in app.subscribers_users
            if callback.message.chat.type == "private"
            else callback.message.chat.id in app.subscribers_chats
        )
        is_admin = callback.from_user.id == ADMIN_ID
        await callback.message.edit_text(f"{app.title}", reply_markup=get_app_menu(app, is_subscribed, is_admin))
        logger.info(f"Пользователь {callback.from_user.id} выбрал приложение: {key}")
    except Exception as e:
        logger.error(f"Ошибка при выборе приложения: {e}")
        await callback.message.edit_text("Произошла ошибка.")

@router.callback_query(F.data == "back")
async def go_back(callback: CallbackQuery):
    try:
        apps = get_all_apps()
        if not apps:
            await callback.message.edit_text("Пока нет доступных приложений.")
            return
        await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu(apps))
        logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")
    except Exception as e:
        logger.error(f"Ошибка при возврате в меню: {e}")
        await callback.message.edit_text("Произошла ошибка.")

@router.callback_query(F.data.startswith("download:"))
async def download_app(callback: CallbackQuery, bot: Bot):
    try:
        key = callback.data.split(":", 1)[1]
        app = get_app(key)
        if not app:
            await callback.message.edit_text("Приложение не найдено.")
            return
        release = await get_latest_release(app.repo)
        if not release:
            await callback.message.edit_text("Релизы для этого приложения не найдены.")
            return
        is_subscribed = (
            callback.from_user.id in app.subscribers_users
            if callback.message.chat.type == "private"
            else callback.message.chat.id in app.subscribers_chats
        )
        is_admin = callback.from_user.id == ADMIN_ID
        sent = False
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        headers["Accept"] = "application/octet-stream"
        async with aiohttp.ClientSession() as session:
            for asset in release['assets']:
                if any(asset['name'].endswith(f.strip()) for f in app.asset_filters):
                    asset_url = asset['url']
                    logger.info(f"Загрузка файла: {asset_url} (имя: {asset['name']})")
                    try:
                        async with session.get(asset_url, headers=headers) as resp:
                            if resp.status != 200:
                                logger.error(f"Файл недоступен: {asset_url}, статус {resp.status}")
                                continue
                            file_data = await resp.read()
                            await bot.send_document(
                                chat_id=callback.message.chat.id,
                                document=BufferedInputFile(file_data, filename=asset['name']),
                                caption=f"{app.title}: {release['name']}\n{release.get('body', 'Описание релиза отсутствует.')}"
                            )
                            sent = True
                            logger.info(f"Отправлен файл {asset['name']} для {app.title} в чат {callback.message.chat.id}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке файла {asset['name']}: {e}")
                        continue
        if not sent:
            await callback.message.edit_text("Подходящие файлы для скачивания не найдены или недоступны.")
        await callback.message.edit_text(f"{app.title}", reply_markup=get_app_menu(app, is_subscribed, is_admin))
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await callback.message.edit_text("Произошла ошибка.")

@router.callback_query(F.data.startswith("link:"))
async def send_link(callback: CallbackQuery):
    try:
        key = callback.data.split(":", 1)[1]
        app = get_app(key)
        if not app:
            await callback.message.edit_text("Приложение не найдено.")
            return
        is_subscribed = (
            callback.from_user.id in app.subscribers_users
            if callback.message.chat.type == "private"
            else callback.message.chat.id in app.subscribers_chats
        )
        is_admin = callback.from_user.id == ADMIN_ID
        await callback.message.edit_text(f"{app.title}\n{app.link}", reply_markup=get_app_menu(app, is_subscribed, is_admin))
        logger.info(f"Отправлена ссылка для {app.title} пользователю {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке ссылки: {e}")
        await callback.message.edit_text("Произошла ошибка.")

@router.callback_query(F.data.startswith("subscribe:"))
async def toggle_subscription(callback: CallbackQuery):
    try:
        key = callback.data.split(":", 1)[1]
        app = get_app(key)
        if not app:
            await callback.message.edit_text("Приложение не найдено.")
            return
        is_admin = callback.from_user.id == ADMIN_ID
        if callback.message.chat.type == "private":
            if callback.from_user.id in app.subscribers_users:
                app.subscribers_users.remove(callback.from_user.id)
                await callback.message.edit_text(f"Вы отписались от {app.title}")
                logger.info(f"Пользователь {callback.from_user.id} отписался от {app.title}")
            else:
                app.subscribers_users.append(callback.from_user.id)
                await callback.message.edit_text(f"Вы подписались на {app.title}")
                logger.info(f"Пользователь {callback.from_user.id} подписался на {app.title}")
            save_app(app)
        else:
            chat_member = await callback.message.chat.get_member(callback.from_user.id)
            if chat_member.status not in ["administrator", "creator"]:
                await callback.message.edit_text("Только администраторы группы могут управлять подпиской.")
                return
            if callback.message.chat.id in app.subscribers_chats:
                app.subscribers_chats.remove(callback.message.chat.id)
                await callback.message.edit_text(f"Чат отписан от {app.title}")
                logger.info(f"Чат {callback.message.chat.id} отписан от {app.title}")
            else:
                app.subscribers_chats.append(callback.message.chat.id)
                await callback.message.edit_text(f"Чат подписан на {app.title}")
                logger.info(f"Чат {callback.message.chat.id} подписан на {app.title}")
            save_app(app)
        is_subscribed = (
            callback.from_user.id in app.subscribers_users
            if callback.message.chat.type == "private"
            else callback.message.chat.id in app.subscribers_chats
        )
        await callback.message.edit_reply_markup(reply_markup=get_app_menu(app, is_subscribed, is_admin))
    except Exception as e:
        logger.error(f"Ошибка при управлении подпиской: {e}")
        await callback.message.edit_text("Произошла ошибка.")

@router.callback_query(F.data.startswith("setrepo:"))
async def set_repo_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.message.edit_text("Только глобальный администратор может устанавливать репозитории.")
        return
    key = callback.data.split(":", 1)[1]
    app = get_app(key)
    if not app:
        await callback.message.edit_text("Приложение не найдено.")
        return
    await callback.message.edit_text("Введите новый GitHub-репозиторий (формат: owner/repo, например, 'LSPosed/LSPosed'):")
    await state.update_data(key=key)
    await state.set_state(AddAppStates.repo)
    logger.info(f"Админ {callback.from_user.id} начал установку репозитория для {key}")

@router.callback_query(F.data.startswith("delete:"))
async def delete_app_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.message.edit_text("Только глобальный администратор может удалять приложения.")
        return
    key = callback.data.split(":", 1)[1]
    if get_app(key):
        delete_app(key)
        await callback.message.edit_text(f"Приложение {key} удалено!")
        apps = get_all_apps()
        await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu(apps))
        logger.info(f"Админ {callback.from_user.id} удалил приложение: {key}")
    else:
        await callback.message.edit_text("Приложение не найдено.")