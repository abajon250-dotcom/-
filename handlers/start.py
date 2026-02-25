from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
import logging

router = Router()

# Пытаемся импортировать всё необходимое, но если не получается – используем заглушки
try:
    from database import add_user, get_user
    from handlers.payment import get_main_menu_keyboard
    from logger import log_action
    DB_OK = True
except ImportError as e:
    logging.error(f"Ошибка импорта в start.py: {e}")
    DB_OK = False

    # Заглушка для клавиатуры на случай ошибки
    def get_main_menu_keyboard():
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="👤 Профиль", callback_data="profile")
        builder.button(text="💰 Купить подписку", callback_data="buy_subscription")
        builder.adjust(1)
        return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Пытаемся добавить пользователя в БД и получить информацию
    reg_date = "неизвестно"
    if DB_OK:
        try:
            await add_user(user_id, username, first_name, last_name)
            user_info = await get_user(user_id)
            if user_info and user_info.get('registered_at'):
                reg_date = datetime.fromisoformat(user_info['registered_at']).strftime("%d.%m.%Y %H:%M")
        except Exception as e:
            logging.error(f"Ошибка при работе с БД в start.py: {e}")
    else:
        # Если импорт не удался, просто продолжаем без БД
        pass

    text = (
        f"👋 <b>Добро пожаловать, {first_name}!</b>\n\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"📛 <b>Username:</b> @{username}\n"
        f"📅 <b>Зарегистрирован:</b> {reg_date}\n\n"
        f"Выбери действие в меню ниже 👇"
    )

    if DB_OK:
        try:
            log_action(user_id, "start")
        except:
            pass

    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())