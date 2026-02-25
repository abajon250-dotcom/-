from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_IDS
from database import (
    get_accounts, get_campaigns, get_users_count,
    get_active_subscriptions_count, get_expired_subscriptions_count,
    get_inactive_users_count, block_user, unblock_user, get_user,
    get_replenishments_stats, get_subscription_purchases_stats,
    get_landings_count, get_campaigns_count, get_templates_count,
    get_active_subscriptions_list
)
import os

router = Router()

class BlockUserState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_action = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Общая статистика", callback_data="admin_stats")
    builder.button(text="📋 Аккаунты", callback_data="admin_accounts")
    builder.button(text="💰 Финансы", callback_data="admin_finance")
    builder.button(text="📦 Контент", callback_data="admin_content")
    builder.button(text="👥 Пользователи", callback_data="admin_users_stats")
    builder.button(text="🚫 Блокировка", callback_data="admin_block_user")
    builder.button(text="📝 Логи", callback_data="admin_logs")
    builder.button(text="🗑 Очистить логи", callback_data="admin_clear_logs")
    builder.adjust(2, 2, 2, 2)
    await message.answer("🔐 Админ-панель", reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    campaigns = await get_campaigns_count()
    landings = await get_landings_count()
    templates = await get_templates_count()
    users = await get_users_count()
    active_subs = await get_active_subscriptions_count()
    expired_subs = await get_expired_subscriptions_count()
    inactive = await get_inactive_users_count()
    text = (
        f"📊 <b>Общая статистика</b>\n\n"
        f"👤 Пользователей: {users}\n"
        f"✅ Активных подписок: {active_subs}\n"
        f"⏳ Просроченных подписок: {expired_subs}\n"
        f"❌ Без подписки: {inactive}\n\n"
        f"📦 Контент:\n"
        f"   • Лендингов: {landings}\n"
        f"   • Кампаний: {campaigns}\n"
        f"   • Шаблонов: {templates}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_finance")
async def admin_finance(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    replenish = await get_replenishments_stats()
    purchases = await get_subscription_purchases_stats()
    text = (
        f"💰 <b>Финансовая статистика</b>\n\n"
        f"💸 Пополнения баланса:\n"
        f"   • Количество: {replenish['count']}\n"
        f"   • Сумма: {replenish['total']:.2f} USDT\n"
        f"   • Средний чек: {replenish['total']/replenish['count'] if replenish['count'] else 0:.2f} USDT\n\n"
        f"🛒 Покупки подписки:\n"
        f"   • Количество: {purchases['count']}\n"
        f"   • Сумма: {purchases['total']:.2f} USDT\n"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_content")
async def admin_content(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    landings = await get_landings_count()
    campaigns = await get_campaigns_count()
    templates = await get_templates_count()
    text = (
        f"📦 <b>Контент</b>\n\n"
        f"🌐 Лендингов создано: {landings}\n"
        f"🚀 Кампаний запущено: {campaigns}\n"
        f"📝 Шаблонов создано: {templates}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_users_stats")
async def admin_users_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    total = await get_users_count()
    active_subs = await get_active_subscriptions_count()
    expired_subs = await get_expired_subscriptions_count()
    inactive = await get_inactive_users_count()
    text = (
        f"👥 <b>Статистика пользователей</b>\n\n"
        f"👤 Всего пользователей: {total}\n"
        f"✅ Активных подписок: {active_subs}\n"
        f"⏳ Просроченных подписок: {expired_subs}\n"
        f"❌ Без подписки: {inactive}\n\n"
        f"🔍 Для просмотра активных подписок нажмите кнопку ниже."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Активные подписки", callback_data="admin_active_subs")
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(1)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_active_subs")
async def admin_active_subs(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    subs = await get_active_subscriptions_list()
    if not subs:
        text = "📋 Нет активных подписок."
    else:
        text = "📋 <b>Активные подписки</b>\n\n"
        for sub in subs:
            user = await get_user(sub["user_id"])
            username = user["username"] if user and user["username"] else "нет"
            text += f"🆔 {sub['user_id']} (@{username}) – до {sub['expires_at'][:10]}\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_users_stats")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_accounts")
async def admin_accounts(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    accounts = await get_accounts()
    text = "📋 Аккаунты:\n"
    for acc in accounts:
        text += f"ID {acc['id']}: {acc['platform']} - {acc['status']}\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_block_user")
async def admin_block_user(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🚫 Введи Telegram ID пользователя, которого нужно заблокировать/разблокировать:",
        reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin_back").as_markup()
    )
    await state.set_state(BlockUserState.waiting_for_user_id)
    await callback.answer()

@router.message(BlockUserState.waiting_for_user_id)
async def block_user_id_received(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except:
        await message.answer("❌ Неверный ID. Введи число.")
        return
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь с таким ID не найден.")
        await state.clear()
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Разблокировать", callback_data=f"unblock_{user_id}")
    builder.button(text="❌ Заблокировать", callback_data=f"block_{user_id}")
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await message.answer(
        f"👤 Пользователь: {user['first_name']} (@{user['username']})\n"
        f"Статус блокировки: {'🚫 Заблокирован' if user['is_blocked'] else '✅ Активен'}",
        reply_markup=builder.as_markup()
    )
    await state.clear()

@router.callback_query(F.data.startswith("block_"))
async def process_block(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split("_")[1])
    await block_user(user_id)
    await callback.message.edit_text(f"✅ Пользователь {user_id} заблокирован.")
    await callback.answer()

@router.callback_query(F.data.startswith("unblock_"))
async def process_unblock(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split("_")[1])
    await unblock_user(user_id)
    await callback.message.edit_text(f"✅ Пользователь {user_id} разблокирован.")
    await callback.answer()

@router.callback_query(F.data == "admin_logs")
async def admin_logs(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    try:
        with open('user_actions.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()[-20:]
        log_text = "📝 Последние логи:\n" + "".join(lines)
    except FileNotFoundError:
        log_text = "Лог-файл не найден."
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(log_text[:3000], reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_clear_logs")
async def admin_clear_logs(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    try:
        open('user_actions.log', 'w').close()
        await callback.message.edit_text("✅ Логи очищены.")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Общая статистика", callback_data="admin_stats")
    builder.button(text="📋 Аккаунты", callback_data="admin_accounts")
    builder.button(text="💰 Финансы", callback_data="admin_finance")
    builder.button(text="📦 Контент", callback_data="admin_content")
    builder.button(text="👥 Пользователи", callback_data="admin_users_stats")
    builder.button(text="🚫 Блокировка", callback_data="admin_block_user")
    builder.button(text="📝 Логи", callback_data="admin_logs")
    builder.button(text="🗑 Очистить логи", callback_data="admin_clear_logs")
    builder.adjust(2, 2, 2, 2)
    await callback.message.edit_text("🔐 Админ-панель", reply_markup=builder.as_markup())
    await callback.answer()