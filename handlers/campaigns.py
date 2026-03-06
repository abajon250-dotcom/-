from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from database import get_user_accounts_by_platform, get_templates, get_template, get_account
from services.telegram_sender import TelegramSender
from services.vk_sender import VKSender
from services.vk_friends import VKFriendManager
from utils.decorators import subscription_required, admin_required
import asyncio

router = Router()

class CampaignStates(StatesGroup):
    waiting_platform = State()
    waiting_account = State()
    waiting_target = State()
    waiting_users = State()
    waiting_template = State()
    waiting_delay = State()

@router.callback_query(F.data == "campaigns_menu")
@subscription_required
async def campaigns_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Telegram", callback_data="platform_telegram")],
        [InlineKeyboardButton(text="📘 VK", callback_data="platform_vk")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    await callback.message.edit_text("Выберите платформу для рассылки:", reply_markup=kb)
    await state.set_state(CampaignStates.waiting_platform)
    await callback.answer()

@router.callback_query(StateFilter(CampaignStates.waiting_platform), F.data.startswith("platform_"))
async def process_platform(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split("_")[1]  # 'telegram' или 'vk'
    await state.update_data(platform=platform)
    accounts = await get_user_accounts_by_platform(callback.from_user.id, platform)
    if not accounts:
        await callback.message.edit_text(
            f"❌ У вас нет добавленных аккаунтов для {platform}. Сначала добавьте аккаунт.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="list_accounts")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="campaigns_menu")]
            ])
        )
        await state.clear()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for acc in accounts:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"Аккаунт #{acc['id']}", callback_data=f"account_{acc['id']}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="campaigns_menu")])
    await callback.message.edit_text("Выберите аккаунт для рассылки:", reply_markup=kb)
    await state.set_state(CampaignStates.waiting_account)
    await callback.answer()

@router.callback_query(StateFilter(CampaignStates.waiting_account), F.data.startswith("account_"))
async def process_account(callback: CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[1])
    await state.update_data(account_id=account_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всем друзьям (VK)", callback_data="target_friends")],
        [InlineKeyboardButton(text="📋 Свой список", callback_data="target_custom")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="campaigns_menu")]
    ])
    await callback.message.edit_text("Выберите получателей:", reply_markup=kb)
    await state.set_state(CampaignStates.waiting_target)
    await callback.answer()

@router.callback_query(StateFilter(CampaignStates.waiting_target), F.data.startswith("target_"))
async def process_target(callback: CallbackQuery, state: FSMContext):
    target_type = callback.data.split("_")[1]  # 'friends' или 'custom'
    await state.update_data(target_type=target_type)
    if target_type == 'custom':
        await callback.message.edit_text(
            "Введите список получателей (каждый ID с новой строки):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="campaigns_menu")]
            ])
        )
        await state.set_state(CampaignStates.waiting_users)
    else:
        await show_templates(callback, state)
    await callback.answer()

@router.message(StateFilter(CampaignStates.waiting_users))
async def process_users(message: Message, state: FSMContext):
    users = [line.strip() for line in message.text.split('\n') if line.strip()]
    await state.update_data(users=users)
    await show_templates(message, state)

async def show_templates(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    platform = data['platform']
    templates = await get_templates(platform=platform, user_id=event.from_user.id)
    if not templates:
        await event.answer("У вас нет шаблонов для этой платформы. Сначала создайте шаблон.", show_alert=True)
        await state.clear()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for t in templates:
        kb.inline_keyboard.append([InlineKeyboardButton(text=t['name'], callback_data=f"template_{t['id']}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="campaigns_menu")])
    if isinstance(event, CallbackQuery):
        await event.message.edit_text("Выберите шаблон для рассылки:", reply_markup=kb)
    else:
        await event.answer("Выберите шаблон для рассылки:", reply_markup=kb)
    await state.set_state(CampaignStates.waiting_template)

@router.callback_query(StateFilter(CampaignStates.waiting_template), F.data.startswith("template_"))
async def process_template(callback: CallbackQuery, state: FSMContext):
    template_id = int(callback.data.split("_")[1])
    await state.update_data(template_id=template_id)
    await callback.message.edit_text(
        "Введите задержку между сообщениями в секундах (по умолчанию 1):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="campaigns_menu")]
        ])
    )
    await state.set_state(CampaignStates.waiting_delay)
    await callback.answer()

@router.message(StateFilter(CampaignStates.waiting_delay))
async def process_delay(message: Message, state: FSMContext):
    try:
        delay = float(message.text)
    except ValueError:
        delay = 1.0
    data = await state.get_data()
    platform = data['platform']
    account_id = data['account_id']
    target_type = data['target_type']
    template_id = data['template_id']

    # Получаем шаблон и аккаунт
    template = await get_template(template_id)
    if not template:
        await message.answer("❌ Шаблон не найден.")
        await state.clear()
        return
    account = await get_account(account_id)
    if not account:
        await message.answer("❌ Аккаунт не найден.")
        await state.clear()
        return

    # Получаем список получателей
    if target_type == 'friends':
        if platform == 'vk':
            cred = account['credentials']
            manager = VKFriendManager(cred['access_token'])
            users = manager.get_friends()
            if not users:
                await message.answer("❌ Не удалось получить список друзей.")
                await state.clear()
                return
        else:
            # Для Telegram "друзья" пока не реализованы
            await message.answer("❌ Для Telegram пока поддерживается только свой список.")
            await state.clear()
            return
    else:
        users = data['users']

    await message.answer(f"⏳ Запускаю рассылку через {platform}...")

    if platform == 'telegram':
        cred = account['credentials']
        sender = TelegramSender(cred['session_string'])
        await sender.start()
        try:
            success = await sender.send_to_users(users, template['text'], delay)
        finally:
            await sender.stop()
    else:  # vk
        cred = account['credentials']
        sender = VKSender(cred['access_token'])
        success = sender.send_to_users(users, template['text'], delay)

    await message.answer(f"✅ Рассылка завершена. Успешно отправлено: {success}/{len(users)}")
    await state.clear()