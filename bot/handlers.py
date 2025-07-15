from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="LSPosed", callback_data="lsposed")],
        [InlineKeyboardButton(text="PlayIntegrityFix", callback_data="pif")],
        [InlineKeyboardButton(text="🔧 Другие", callback_data="others")],
    ])

def module_menu(module: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Скачать", callback_data=f"{module}_download")],
        [InlineKeyboardButton(text="🌐 Ссылка на проект", callback_data=f"{module}_link")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])

def register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def handle_start(message: Message):
        await message.answer("Привет! Выбери модуль:", reply_markup=main_menu())

    @dp.callback_query(F.data.in_({"lsposed", "pif", "others"}))
    async def handle_module(callback: CallbackQuery):
        await callback.message.edit_text(
            f"{callback.data.upper()}:\nВыбери действие:",
            reply_markup=module_menu(callback.data)
        )
        await callback.answer()

    @dp.callback_query(F.data.endswith("_download"))
    async def handle_download(callback: CallbackQuery):
        module = callback.data.replace("_download", "")
        await callback.message.answer(f"📦 Пока что заглушка для {module} — скоро будет загрузка!")
        await callback.answer()

    @dp.callback_query(F.data.endswith("_link"))
    async def handle_link(callback: CallbackQuery):
        module = callback.data.replace("_link", "")
        links = {
            "lsposed": "https://github.com/LSPosed/LSPosed",
            "pif": "https://github.com/chiteroman/PlayIntegrityFix",
        }
        await callback.message.answer(f"🌐 <b>Ссылка на проект {module.upper()}</b>:\n{links.get(module, 'Неизвестно')}")
        await callback.answer()

    @dp.callback_query(F.data == "back")
    async def handle_back(callback: CallbackQuery):
        await callback.message.edit_text("Привет! Выбери модуль:", reply_markup=main_menu())
        await callback.answer()
