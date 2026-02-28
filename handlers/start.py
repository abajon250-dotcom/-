from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
from database import add_user, get_user
from handlers.payment import get_main_menu_keyboard
from logger import log_action

router = Router()

AVATAR_URL = "https://ibb.co/Df4bBRzz"  # замените на свою ссылку

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    await add_user(user_id, username, first_name, last_name)
    user_info = await get_user(user_id)

    reg_date = datetime.fromisoformat(user_info['registered_at']).strftime("%d.%m.%Y %H:%M") if user_info else "неизвестно"

    text = (
        f"✨ <b>Добро пожаловать в GRSspam!</b> ✨\n\n"
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"📛 <b>Username:</b> @{username}\n"
        f"📅 <b>Регистрация:</b> {reg_date}\n\n"
        f"🚀 <b>Возможности бота:</b>\n"
        f"• Создание стильных лендингов с фото\n"
        f"• Подключение аккаунтов Telegram, VK, MAX\n"
        f"• Гибкая система подписок и внутренний баланс\n"
        f"• Рассылки и шаблоны\n"
        f"• Поддержка 24/7\n\n"
        f"👇 <b>Выбери действие в меню ниже</b>"
    )

    log_action(user_id, "start")

    try:
        await message.answer_photo(
            photo=AVATAR_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())