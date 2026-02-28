from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from config import ADMIN_IDS
from database import (
    get_accounts, get_campaigns, get_users_count,
    get_active_subscriptions_count, get_expired_subscriptions_count,
    get_inactive_users_count, block_user, unblock_user, get_user,
    set_subscription, get_all_users, get_landings_count,
    get_campaigns_count, get_templates_count
)
from handlers.common import get_nav_keyboard
import asyncio
import os

router = Router()

class BlockUserState(StatesGroup):
    waiting_for_user_id = State()

class GiveSubscriptionState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_days = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

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
    builder.button(text="📦 Контент", callback_data="admin_content")
    builder.button(text="👥 Пользователи", callback_data="admin_users_stats")
    builder.button(text="🚫 Блокировка", callback_data="admin_block_user")
    builder.button(text="🎁 Выдать подписку", callback_data="admin_give_subscription")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="📝 Логи", callback_data="admin_logs")
    builder.button(text="🗑 Очистить логи", callback_data="admin_clear_logs")
    builder.adjust(2, 2, 2, 3)
    await message.answer("🔐 Админ-панель", reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    campaigns = await get_campaigns()
    total = len(campaigns)
    text = f"📊 Статистика кампаний:\nВсего кампаний: {total}\n"
    if total > 0:
        text += f"Последняя: {campaigns[0]['created_at']}"
    else:
        text += "Кампаний пока нет."
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
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
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
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
        f"❌ Без подписки: {inactive}"
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
    from database import get_active_subscriptions_list
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

# ----- Блокировка -----
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

# ----- Выдача подписки -----
@router.callback_query(F.data == "admin_give_subscription")
async def admin_give_subscription_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(
        "🔹 Введите Telegram ID пользователя, которому хотите выдать подписку:",
        reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin_back").as_markup()
    )
    await state.set_state(GiveSubscriptionState.waiting_for_user_id)
    await callback.answer()

@router.message(GiveSubscriptionState.waiting_for_user_id)
async def admin_give_subscription_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except:
        await message.answer("❌ Неверный ID. Введите число.")
        return
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь с таким ID не найден.")
        await state.clear()
        return
    await state.update_data(target_user_id=user_id)
    await message.answer(
        "🔹 Введите количество дней подписки (целое число):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(GiveSubscriptionState.waiting_for_days)

@router.message(GiveSubscriptionState.waiting_for_days)
async def admin_give_subscription_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введите положительное целое число.")
        return
    data = await state.get_data()
    user_id = data['target_user_id']
    expires_at = datetime.now() + timedelta(days=days)
    await set_subscription(user_id, "active", expires_at.isoformat(), "admin_grant")
    await message.answer(f"✅ Подписка на {days} дней выдана пользователю {user_id}.")
    await state.clear()
    await admin_panel(message)

# ----- Рассылка -----
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text(
        "📢 Введите сообщение для рассылки всем пользователям (можно использовать HTML-разметку):",
        reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="admin_back").as_markup()
    )
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()

@router.message(BroadcastState.waiting_for_message)
async def admin_broadcast_message(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    text = message.text
    users = await get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей в базе.")
        await state.clear()
        return
    await message.answer(f"✅ Начинаю рассылку {len(users)} пользователям...")
    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(chat_id=user['user_id'], text=text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            print(f"Не удалось отправить {user['user_id']}: {e}")
            failed += 1
        await asyncio.sleep(0.05)
    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent}, ошибок: {failed}.")
    await state.clear()
    await admin_panel(message)

# ----- Логи -----
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
    builder.button(text="📦 Контент", callback_data="admin_content")
    builder.button(text="👥 Пользователи", callback_data="admin_users_stats")
    builder.button(text="🚫 Блокировка", callback_data="admin_block_user")
    builder.button(text="🎁 Выдать подписку", callback_data="admin_give_subscription")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="📝 Логи", callback_data="admin_logs")
    builder.button(text="🗑 Очистить логи", callback_data="admin_clear_logs")
    builder.adjust(2, 2, 2, 3)
    await callback.message.edit_text("🔐 Админ-панель", reply_markup=builder.as_markup())
    await callback.answer()