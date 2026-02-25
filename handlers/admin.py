from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_IDS
from database import get_accounts, get_campaigns
import os

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📋 Аккаунты", callback_data="admin_accounts")
    builder.button(text="📝 Логи", callback_data="admin_logs")
    builder.button(text="🗑 Очистить логи", callback_data="admin_clear_logs")
    builder.adjust(1)
    await message.answer("🔐 Админ-панель", reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    campaigns = await get_campaigns()
    total = len(campaigns)
    text = f"📊 Статистика:\nВсего кампаний: {total}\n"
    if total > 0:
        text += f"Последняя: {campaigns[0]['created_at']}"
    else:
        text += "Кампаний пока нет."
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

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

@router.callback_query(F.data == "admin_clear_logs")
async def admin_clear_logs(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    try:
        open('user_actions.log', 'w').close()
        await callback.message.edit_text("✅ Логи очищены.")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📋 Аккаунты", callback_data="admin_accounts")
    builder.button(text="📝 Логи", callback_data="admin_logs")
    builder.button(text="🗑 Очистить логи", callback_data="admin_clear_logs")
    builder.adjust(1)
    await callback.message.edit_text("🔐 Админ-панель", reply_markup=builder.as_markup())