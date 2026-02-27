from aiogram import Router, types, F
from handlers.payment import get_accounts_reply_keyboard

router = Router()

@router.callback_query(F.data == "accounts_menu")
async def accounts_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("✅ Тест: кнопка Аккаунты работает!", reply_markup=get_accounts_reply_keyboard())
    await callback.answer()