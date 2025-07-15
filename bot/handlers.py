from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext


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
    async def handle_start(message: Message, state: FSMContext):
        sent = await message.answer("Главное меню:", reply_markup=main_menu())
        await state.update_data(menu_message_id=sent.message_id, current_module=None)

    @dp.callback_query(F.data.in_({"lsposed", "pif", "others"}))
    async def handle_module(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        menu_msg_id = data.get("menu_message_id")

        try:
            await callback.message.edit_text(
                f"{callback.data.upper()}:\nВыбери действие:",
                reply_markup=module_menu(callback.data)
            )
            await state.update_data(current_module=callback.data)
        except:
            sent = await callback.message.answer(
                f"{callback.data.upper()}:\nВыбери действие:",
                reply_markup=module_menu(callback.data)
            )
            await state.update_data(menu_message_id=sent.message_id, current_module=callback.data)

        await callback.answer()

    @dp.callback_query(F.data.endswith("_download"))
    async def handle_download(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        menu_msg_id = data.get("menu_message_id")
        current_module = data.get("current_module")
        chat_id = callback.message.chat.id

        if menu_msg_id:
            try:
                await callback.bot.delete_message(chat_id, menu_msg_id)
            except:
                pass

        module = callback.data.replace("_download", "")
        await callback.message.answer(f"📦 Пока что заглушка для {module} — скоро будет загрузка!")

        if current_module:
            sent = await callback.message.answer(
                f"{current_module.upper()}:\nВыбери действие:",
                reply_markup=module_menu(current_module)
            )
        else:
            sent = await callback.message.answer("Главное меню:", reply_markup=main_menu())

        await state.update_data(menu_message_id=sent.message_id)
        await callback.answer()

    @dp.callback_query(F.data.endswith("_link"))
    async def handle_link(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        menu_msg_id = data.get("menu_message_id")
        current_module = data.get("current_module")
        chat_id = callback.message.chat.id

        if menu_msg_id:
            try:
                await callback.bot.delete_message(chat_id, menu_msg_id)
            except:
                pass

        module = callback.data.replace("_link", "")
        links = {
            "lsposed": "https://github.com/LSPosed/LSPosed",
            "pif": "https://github.com/chiteroman/PlayIntegrityFix",
        }

        await callback.message.answer(
            f"🌐 <b>Ссылка на проект {module.upper()}</b>:\n{links.get(module, 'Неизвестно')}",
            disable_web_page_preview=False
        )

        if current_module:
            sent = await callback.message.answer(
                f"{current_module.upper()}:\nВыбери действие:",
                reply_markup=module_menu(current_module)
            )
        else:
            sent = await callback.message.answer("Главное меню:", reply_markup=main_menu())

        await state.update_data(menu_message_id=sent.message_id)
        await callback.answer()

    @dp.callback_query(F.data == "back")
    async def handle_back(callback: CallbackQuery, state: FSMContext):
        try:
            await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
        except:
            sent = await callback.message.answer("Главное меню:", reply_markup=main_menu())
            await state.update_data(menu_message_id=sent.message_id)
        await state.update_data(current_module=None)
        await callback.answer()
