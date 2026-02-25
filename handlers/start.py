from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
from database import add_user, get_user
from handlers.payment import get_main_menu_keyboard
from logger import log_action

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    await add_user(user_id, username, first_name, last_name)
    user_info = await get_user(user_id)

    reg_date = datetime.fromisoformat(user_info['registered_at']).strftime("%d.%m.%Y %H:%M") if user_info else "неизвестно"

    # Текст приветствия (HTML)
    text = (
        f"✨ <b>Добро пожаловать, {first_name}!</b> ✨\n\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"📛 <b>Username:</b> @{username}\n"
        f"📅 <b>Регистрация:</b> {reg_date}\n\n"
        f"🚀 <b>Этот бот умеет:</b>\n"
        f"• Создавать крутые лендинги с фото\n"
        f"• Подключать аккаунты Telegram, VK, MAX\n"
        f"• Запускать массовые рассылки\n"
        f"• Управлять балансом и подпиской\n\n"
        f"👇 <b>Выбери действие в меню ниже</b>"
    )

    log_action(user_id, "start")

    # Отправляем фото (аватарку) вместе с текстом
    # Используем стандартную картинку-заглушку, можно заменить на реальную ссылку
    photo_url = "https://i.imgur.com/YourBotAvatar.png"  # замени на свою ссылку
    await message.answer_photo(
        photo=photo_url,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )