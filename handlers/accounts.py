import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import add_account, is_user_blocked
from services.telegram_auth import TelegramAuth
from services.vk_auth import VkAuth
from logger import log_action
from handlers.common import get_nav_keyboard

router = Router()

class AddAccountState(StatesGroup):
    platform = State()
    phone = State()
    waiting_for_code = State()
    waiting_for_2fa = State()
    auth_instance = State()

# ----- Обработчики текстовых кнопок (из reply-меню) -----
@router.message(F.text == "✈️ Telegram")
async def telegram_account_start(message: types.Message, state: FSMContext):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    await state.update_data(platform="telegram")
    await message.answer(
        "Введи номер телефона в международном формате (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.message(F.text == "📘 VK")
async def vk_account_start(message: types.Message, state: FSMContext):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    await state.update_data(platform="vk")
    await message.answer(
        "Введи номер телефона в международном формате (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.message(F.text == "📱 MAX")
async def max_account_start(message: types.Message, state: FSMContext):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    await state.update_data(platform="max")
    await message.answer(
        "Введи номер телефона для MAX (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

# ----- Обработчик для кнопки "Назад в меню" -----
@router.message(F.text == "◀️ Назад в меню")
async def back_to_main_menu(message: types.Message):
    from handlers.start import cmd_start
    await cmd_start(message)

# ----- (Опционально) Обработчики инлайн-кнопок на случай, если они где-то используются -----
@router.callback_query(F.data == "platform_telegram")
async def telegram_chosen(callback: types.CallbackQuery, state: FSMContext):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    await state.update_data(platform="telegram")
    await callback.message.edit_text(
        "Введи номер телефона в международном формате (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.callback_query(F.data == "platform_vk")
async def vk_chosen(callback: types.CallbackQuery, state: FSMContext):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    await state.update_data(platform="vk")
    await callback.message.edit_text(
        "Введи номер телефона в международном формате (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.callback_query(F.data == "platform_max")
async def max_chosen(callback: types.CallbackQuery, state: FSMContext):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    await state.update_data(platform="max")
    await callback.message.edit_text(
        "Введи номер телефона для MAX (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

# ----- Общий обработчик ввода номера -----
@router.message(AddAccountState.phone)
async def phone_entered(message: types.Message, state: FSMContext):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    phone = message.text.strip()
    if not re.match(r'^\+\d{10,15}$', phone):
        await message.answer(
            "❌ Неверный формат номера. Введи номер в международном формате, например +79001234567",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return

    data = await state.get_data()
    platform = data["platform"]

    if platform == "max":
        await add_account(platform, {"phone": phone})
        await message.answer("✅ Аккаунт MAX добавлен. Убедись, что устройство подключено и приложение авторизовано.")
        await state.clear()
        from handlers.start import cmd_start
        await cmd_start(message)
        return

    try:
        if platform == "telegram":
            auth = TelegramAuth(phone)
            await auth.send_code()
        else:
            auth = VkAuth(phone)
            await auth.send_code()

        await state.update_data(auth_instance=auth, phone=phone)

        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="back_to_phone")
        builder.button(text="🚫 Отмена", callback_data="cancel")
        builder.adjust(1)

        await message.answer(
            "На твой телефон отправлен код. Введи его цифрами:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(AddAccountState.waiting_for_code)
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке кода: {e}")
        await state.clear()

@router.callback_query(F.data == "back_to_phone", AddAccountState.waiting_for_code)
async def back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    await state.set_state(AddAccountState.phone)
    await callback.message.edit_text(
        "Введи номер телефона заново:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )

@router.message(AddAccountState.waiting_for_code)
async def code_entered(message: types.Message, state: FSMContext):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    code = message.text.strip()
    data = await state.get_data()
    auth = data["auth_instance"]
    platform = data["platform"]

    try:
        result = await auth.check_code(code)
        if result is True:
            await finalize_login(message, state, auth, platform)
        elif result == "2fa_required":
            await message.answer(
                "Введи двухфакторный пароль (если он установлен):",
                reply_markup=get_nav_keyboard(show_cancel=True)
            )
            await state.set_state(AddAccountState.waiting_for_2fa)
        else:
            await message.answer(
                "❌ Неверный код. Попробуй ещё раз.",
                reply_markup=get_nav_keyboard(show_cancel=True)
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка при проверке кода: {e}")
        await state.clear()

@router.message(AddAccountState.waiting_for_2fa)
async def twofa_entered(message: types.Message, state: FSMContext):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    twofa = message.text.strip()
    data = await state.get_data()
    auth = data["auth_instance"]

    try:
        await auth.check_2fa(twofa)
        await finalize_login(message, state, auth, data["platform"])
    except Exception as e:
        await message.answer(f"❌ Ошибка при проверке пароля: {e}")
        await state.clear()

async def finalize_login(message: types.Message, state: FSMContext, auth, platform):
    credentials = auth.get_credentials()
    log_action(message.from_user.id, "add_account", f"{platform}: {credentials.get('phone', '')}")
    await add_account(platform, credentials)
    await message.answer(f"✅ Аккаунт {platform} успешно добавлен!")
    await state.clear()
    from handlers.start import cmd_start
    await cmd_start(message)