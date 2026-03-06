from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from database import add_account, get_user_accounts, get_user
from services.telegram_auth import TelegramAuth
from services.vk_auth import VKAuth
from keyboards import back_to_menu_keyboard, cancel_keyboard  # cancel_keyboard определите в keyboards.py

router = Router()

# ---------- Telegram Account ----------
class AddTelegramAccount(StatesGroup):
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()

@router.callback_query(F.data == "add_telegram_account")
async def add_telegram_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📱 Введите номер телефона в международном формате (например, +79123456789):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddTelegramAccount.waiting_phone)
    await callback.answer()

@router.message(StateFilter(AddTelegramAccount.waiting_phone))
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    auth = TelegramAuth()
    await auth.start()
    try:
        await auth.send_code(phone)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()
        return
    await state.update_data(phone=phone, auth=auth)
    await message.answer("🔢 Введите код, который пришёл в Telegram:")
    await state.set_state(AddTelegramAccount.waiting_code)

@router.message(StateFilter(AddTelegramAccount.waiting_code))
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip()
    data = await state.get_data()
    auth: TelegramAuth = data['auth']
    result = await auth.sign_in(code)
    if result == "password_needed":
        await message.answer("🔑 Требуется двухфакторный пароль. Введите его:")
        await state.set_state(AddTelegramAccount.waiting_password)
        return
    elif result == "success":
        session_string = await auth.get_session_string()
        await auth.stop()
        # Сохраняем в БД (platform='telegram')
        credentials = {"session_string": session_string, "phone": data['phone']}
        await add_account(message.from_user.id, "telegram", credentials)
        await message.answer("✅ Аккаунт Telegram успешно добавлен!", reply_markup=back_to_menu_keyboard())
        await state.clear()
    else:
        await message.answer("❌ Неверный код. Попробуйте снова.")
        await state.clear()

@router.message(StateFilter(AddTelegramAccount.waiting_password))
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    auth: TelegramAuth = data['auth']
    try:
        await auth.sign_in_password(password)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()
        return
    session_string = await auth.get_session_string()
    await auth.stop()
    credentials = {"session_string": session_string, "phone": data['phone']}
    await add_account(message.from_user.id, "telegram", credentials)
    await message.answer("✅ Аккаунт Telegram успешно добавлен!", reply_markup=back_to_menu_keyboard())
    await state.clear()

# ---------- VK Account ----------
class AddVKAccount(StatesGroup):
    waiting_token = State()

@router.callback_query(F.data == "add_vk_account")
async def add_vk_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔑 Введите токен доступа VK (получить можно на https://vkhost.github.io/):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddVKAccount.waiting_token)
    await callback.answer()

@router.message(StateFilter(AddVKAccount.waiting_token))
async def process_vk_token(message: Message, state: FSMContext):
    token = message.text.strip()
    user_info = VKAuth.check_token(token)
    if not user_info:
        await message.answer("❌ Неверный токен. Попробуйте снова.")
        await state.clear()
        return
    credentials = {"access_token": token, "vk_user_id": user_info['id']}
    await add_account(message.from_user.id, "vk", credentials)
    await message.answer(
        f"✅ Аккаунт VK для пользователя {user_info['first_name']} {user_info['last_name']} добавлен!",
        reply_markup=back_to_menu_keyboard()
    )
    await state.clear()

# ---------- Список аккаунтов ----------
@router.callback_query(F.data == "list_accounts")
async def list_accounts(callback: CallbackQuery):
    accounts = await get_user_accounts(callback.from_user.id)
    text = "📱 **Ваши аккаунты**\n\n"
    if not accounts:
        text += "У вас пока нет добавленных аккаунтов."
    else:
        for acc in accounts:
            platform = acc['platform']
            cred = acc['credentials']
            if platform == 'telegram':
                text += f"• 📱 Telegram: {cred.get('phone', '—')} ({acc['status']})\n"
            elif platform == 'vk':
                text += f"• 📘 VK: ID {cred.get('vk_user_id', '—')} ({acc['status']})\n"
            else:
                text += f"• {platform}: {cred}\n"
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()