from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_nav_keyboard(show_back=False, show_cancel=True):
    builder = InlineKeyboardBuilder()
    if show_back:
        builder.button(text="◀️ Назад", callback_data="back")
    if show_cancel:
        builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    from handlers.start import cmd_start
    await cmd_start(callback.message)

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import cmd_start
    await cmd_start(callback.message)

@router.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import cmd_start
    await cmd_start(callback.message)