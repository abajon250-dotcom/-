import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import add_account, get_user_accounts, is_user_blocked
from services.telegram_auth import TelegramAuth
from services.vk_auth import VkAuth
from logger import log_action
from handlers.common import get_nav_keyboard
from handlers.payment import get_accounts_reply_keyboard, check_subscription

router = Router()

class AddAccountState(StatesGroup):
    platform = State()
    phone = State()
    waiting_for_code = State()
    waiting_for_2fa = State()
    auth_instance = State()

# ================== Отображение списка аккаунтов ==================
@router.callback_query(F.data == "accounts_menu")
async def accounts_menu_callback(callback: types.CallbackQuery):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    if not await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "❌ Для управления аккаунтами необходима подписка.",
            reply_markup=InlineKeyboardBuilder().button(text="💰 Купить подписку", callback_data="buy_subscription").as_markup()
        )
        await callback.answer()
        return

    user_id = callback.from_user.id
    accounts = await get_user_accounts(user_id)

    if accounts:
        count = len(accounts)
        text = f"📱 <b>Ваши подключённые аккаунты ({count}):</b>\n\n"
        for acc in accounts:
            phone = acc['credentials'].get('phone', 'не указан')
            text += f"• {acc['platform']}: {phone} — статус: {acc['status']}\n"
    else:
        text = "📱 У вас пока нет подключённых аккаунтов."

    # Удаляем старое сообщение (главное меню) и отправляем новое с reply-клавиатурой
    await callback.message.delete()
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_accounts_reply_keyboard()
    )
    await callback.answer()

# ----- Рабочий Telegram -----
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

# ----- Рабочий VK -----
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

# ----- Заглушка MAX (можно сохранить номер, но реальной авторизации нет) -----
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

# ----- Ввод номера (общий для Telegram, VK, MAX) -----
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

    # MAX добавляется сразу без подтверждения
    if platform == "max":
        await add_account(message.from_user.id, platform, {"phone": phone})
        await message.answer("✅ Аккаунт MAX добавлен. Убедись, что устройство подключено и приложение авторизовано.")
        await state.clear()
        from handlers.start import cmd_start
        await cmd_start(message)
        return

    try:
        if platform == "telegram":
            auth = TelegramAuth(phone)
            await auth.send_code()
        elif platform == "vk":
            auth = VkAuth(phone)
            await auth.send_code()
        else:
            await message.answer("❌ Неизвестная платформа")
            await state.clear()
            return

        # Если после send_code уже авторизованы (есть сессия)
        if (platform == "vk" and auth.vk is not None) or (platform == "telegram" and auth.client is not None):
            await finalize_login(message, state, auth, platform)
            return

        # Запрашиваем код
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
        error_text = str(e).lower()
        if "код" in error_text or "code" in error_text or "auth" in error_text:
            # Требуется ввод кода
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
        else:
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
        error_text = str(e)
        if "истёк" in error_text or "expired" in error_text:
            await message.answer(
                "⏳ Код подтверждения истёк. Нажмите «Назад» и запросите код заново.",
                reply_markup=get_nav_keyboard(show_cancel=True)
            )
            await state.clear()
            from handlers.start import cmd_start
            await cmd_start(message)
        else:
            await message.answer(f"❌ Ошибка при проверке кода: {error_text}")
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
    await add_account(message.from_user.id, platform, credentials)
    await message.answer(f"✅ Аккаунт {platform} успешно добавлен!")
    await state.clear()
    from handlers.start import cmd_start
    await cmd_start(message)