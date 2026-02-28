from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Профиль", callback_data="profile")
    return builder.as_markup()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Главное меню", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("Профиль (тест)", reply_markup=get_main_menu_keyboard())
    await callback.answer()