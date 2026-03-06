from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_accounts, get_account
from services.vk_friends import VKFriendManager
from keyboards import back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "view_friends")
async def view_friends_menu(callback: CallbackQuery):
    accounts = await get_user_accounts(callback.from_user.id)
    vk_accounts = [acc for acc in accounts if acc['platform'] == 'vk']
    if not vk_accounts:
        await callback.message.edit_text(
            "У вас нет добавленных VK аккаунтов.",
            reply_markup=back_to_menu_keyboard()
        )
        await callback.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for acc in vk_accounts:
        cred = acc['credentials']
        label = f"VK ID {cred.get('vk_user_id', '?')}"
        kb.inline_keyboard.append([InlineKeyboardButton(text=label, callback_data=f"vk_friends_{acc['id']}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    await callback.message.edit_text("Выберите аккаунт для просмотра друзей:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("vk_friends_"))
async def show_vk_friends(callback: CallbackQuery):
    account_id = int(callback.data.split("_")[2])
    account = await get_account(account_id)
    if not account:
        await callback.answer("Аккаунт не найден", show_alert=True)
        return
    cred = account['credentials']
    manager = VKFriendManager(cred['access_token'])
    friends = manager.get_friends()
    text = f"👥 **Друзья VK (ID {cred['vk_user_id']})**:\n\n"
    if not friends:
        text += "Список друзей пуст."
    else:
        # Покажем первые 50
        text += "\n".join(str(uid) for uid in friends[:50])
        if len(friends) > 50:
            text += f"\n... и ещё {len(friends)-50}"
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()