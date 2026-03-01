import re
import asyncio
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database import get_db
from services.account_service import AccountService
from services.telegram_auth import TelegramAuth
from services.vk_auth import VkAuth
from services.tg_contacts import get_tg_stats
from services.vk_friends import get_friends_stats
from logger import log_action
from handlers.common import get_nav_keyboard
from handlers.payment import get_accounts_reply_keyboard, check_subscription
from config import TG_API_ID, TG_API_HASH, PROXY_CONFIG

logger = logging.getLogger(__name__)
router = Router()

class AddAccountState(StatesGroup):
    platform = State()
    phone = State()
    waiting_for_code = State()
    waiting_for_2fa = State()
    auth_instance = State()

@router.callback_query(F.data == "accounts_menu")
async def accounts_menu_callback(callback: types.CallbackQuery):
    # Здесь должна быть проверка подписки и блокировки (опущено для краткости)
    user_id = callback.from_user.id
    db = next(get_db())
    service = AccountService(db)
    accounts = service.get_user_accounts(user_id)
    db.close()

    if accounts:
        text = f"📱 <b>Ваши аккаунты ({len(accounts)}):</b>\n\n"
        for acc in accounts:
            ident = acc.phone or acc.login
            status = "✅ активен" if acc.is_active else "❌ неактивен"
            text += f"• {acc.platform}: {ident} — {status}\n"
    else:
        text = "📱 У вас пока нет подключённых аккаунтов."

    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_accounts_reply_keyboard())
    await callback.answer()

@router.message(F.text == "✈️ Telegram")
async def telegram_start(message: types.Message, state: FSMContext):
    # Проверка подписки/блокировки
    await state.update_data(platform="telegram")
    await message.answer(
        "Введите номер телефона в международном формате (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.message(F.text == "📘 VK")
async def vk_start(message: types.Message, state: FSMContext):
    await state.update_data(platform="vk")
    await message.answer(
        "Введите номер телефона в международном формате (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.message(F.text == "📱 MAX")
async def max_start(message: types.Message, state: FSMContext):
    await state.update_data(platform="max")
    await message.answer(
        "Введите номер телефона для MAX (например, +79001234567):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(AddAccountState.phone)

@router.message(AddAccountState.phone)
async def phone_entered(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not re.match(r'^\+\d{10,15}$', phone):
        await message.answer(
            "❌ Неверный формат. Используйте + и только цифры (например, +79001234567).",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return

    data = await state.get_data()
    platform = data["platform"]

    if platform == "max":
        db = next(get_db())
        service = AccountService(db)
        service.add_max(message.from_user.id, phone)
        db.close()
        await message.answer("✅ Аккаунт MAX добавлен. Убедитесь, что устройство подключено и приложение авторизовано.")
        await state.clear()
        from handlers.start import cmd_start
        await cmd_start(message)
        return

    try:
        if platform == "telegram":
            auth = TelegramAuth(phone)
        elif platform == "vk":
            auth = VkAuth(phone, proxy=PROXY_CONFIG)  # передаём прокси, если есть
        else:
            await message.answer("❌ Неизвестная платформа")
            await state.clear()
            return

        result = await auth.send_code()  # True – уже авторизован, False – код отправлен

        if result is True:
            # Уже есть рабочая сессия
            await finalize_login(message, state, auth, platform)
        else:
            # Код отправлен, переходим к вводу
            await state.update_data(auth_instance=auth, phone=phone)
            builder = InlineKeyboardBuilder()
            builder.button(text="◀️ Назад", callback_data="back_to_phone")
            builder.button(text="🚫 Отмена", callback_data="cancel")
            # Можно добавить кнопку повторной отправки (для VK и Telegram)
            if platform == "telegram":
                builder.button(text="📞 Позвонить", callback_data="resend_telegram_call")
            elif platform == "vk":
                builder.button(text="🔄 Запросить код повторно", callback_data="resend_vk")
            builder.adjust(1)
            await message.answer(
                "На ваш телефон отправлен код. Введите его цифрами:",
                reply_markup=builder.as_markup()
            )
            await state.set_state(AddAccountState.waiting_for_code)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

@router.callback_query(F.data == "back_to_phone", AddAccountState.waiting_for_code)
async def back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddAccountState.phone)
    await callback.message.edit_text(
        "Введите номер заново:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await callback.answer()

@router.callback_query(F.data == "resend_telegram_call", AddAccountState.waiting_for_code)
async def resend_telegram_call(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    auth = data.get("auth_instance")
    if not auth or not hasattr(auth, 'resend_code'):
        await callback.answer("Ошибка: сессия не найдена", show_alert=True)
        return
    try:
        # Здесь должен быть метод resend_code с параметром via_call=True
        # В вашем TelegramAuth можно добавить такой метод
        await auth.resend_code(via_call=True)
        await callback.answer("📞 Запрашиваю звонок...")
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")

@router.callback_query(F.data == "resend_vk", AddAccountState.waiting_for_code)
async def resend_vk(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    auth = data.get("auth_instance")
    if not auth:
        await callback.answer("Ошибка: сессия не найдена", show_alert=True)
        return
    try:
        await auth.resend_code()
        await callback.answer("🔄 Код отправлен повторно")
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")

@router.message(AddAccountState.waiting_for_code)
async def code_entered(message: types.Message, state: FSMContext):
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
                "Введите двухфакторный пароль (если он установлен):",
                reply_markup=get_nav_keyboard(show_cancel=True)
            )
            await state.set_state(AddAccountState.waiting_for_2fa)
        else:
            await message.answer(
                "❌ Неверный код. Попробуйте ещё раз.",
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
    db = next(get_db())
    service = AccountService(db)

    stats_text = ""
    try:
        if platform == "telegram":
            service.add_telegram(
                user_id=message.from_user.id,
                phone=credentials['phone'],
                api_id=credentials['api_id'],
                api_hash=credentials['api_hash'],
                session_path=credentials['session_file']
            )
            tg_stats = await get_tg_stats(credentials['session_file'], credentials['api_id'], credentials['api_hash'])
            if tg_stats:
                stats_text = f"\n📊 Диалогов: {tg_stats['dialogs']}, контактов: {tg_stats['contacts']}"
        elif platform == "vk":
            token = auth.get_token()
            service.add_vk(
                user_id=message.from_user.id,
                login=credentials['login'],
                session_path=credentials['session_file'],
                token=token
            )
            if token:
                vk_stats = await asyncio.to_thread(get_friends_stats, token)
                if vk_stats:
                    stats_text = f"\n📊 Друзей: {vk_stats['total']}"
        elif platform == "max":
            # MAX не требует статистики
            pass
    except Exception as e:
        logger.exception("Ошибка при сохранении или получении статистики")
    finally:
        db.close()

    await message.answer(f"✅ Аккаунт {platform} успешно добавлен!{stats_text}")
    log_action(message.from_user.id, "add_account", f"{platform}: {credentials.get('phone', '')}")
    await state.clear()
    from handlers.start import cmd_start
    await cmd_start(message)

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()