print("🔥 accounts.py загружен!")
from aiogram import Router, types, F
from handlers.payment import get_accounts_reply_keyboard

router = Router()

@router.callback_query(F.data == "accounts_menu")
async def accounts_menu_callback(callback: types.CallbackQuery):
    print("🔥 callback accounts_menu получен!")
    await callback.message.edit_text("✅ Тест: кнопка работает!")
    await callback.answer()