from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Аккаунты", callback_data="accounts_menu")
    return builder.as_markup()

def get_accounts_reply_keyboard():
    kb = [[KeyboardButton(text="✈️ Telegram")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.message()
async def echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")