from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def simple_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="💰 Купить подписку", callback_data="buy_subscription")
    builder.button(text="📱 Аккаунты", callback_data="accounts_menu")
    builder.adjust(1)
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📛 Username: @{message.from_user.username or 'нет'}\n\n"
        f"Выбери действие:",
        reply_markup=simple_menu()
    )