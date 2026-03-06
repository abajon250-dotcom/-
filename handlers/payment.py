import asyncio
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импорты из вашей базы данных
from database import (
    get_subscription, set_subscription,
    add_invoice, update_invoice_status,
    get_balance, update_balance, add_transaction,
    get_user, is_user_blocked
)

# Импорт функций CryptoBot (предполагается, что они асинхронные)
try:
    from services.cryptopay import create_invoice as create_crypto_invoice, check_invoice as check_crypto_invoice
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False
    print("⚠️ CryptoPay не загружен, оплата будет в тестовом режиме")

from config import ADMIN_IDS

router = Router()

# Тарифы подписок
SUBSCRIPTION_TARIFFS = {
    "1day":   {"price": 1.5,  "days": 1,   "label": "1 день"},
    "week":   {"price": 10.0, "days": 7,   "label": "Неделя"},
    "month":  {"price": 30.0, "days": 30,  "label": "Месяц"},
    "forever":{"price": 100.0,"days": 36500, "label": "Навсегда"}
}

# Состояния FSM
class PaymentState(StatesGroup):
    replenish_amount = State()
    replenish_method = State()
    replenish_payment = State()
    choosing_tariff = State()
    choosing_method = State()
    waiting_for_payment = State()

# ---------- Вспомогательные функции ----------
def get_main_menu_keyboard():
    """Главное меню (повтор из вашего кода)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="💰 Купить подписку", callback_data="buy_subscription")
    builder.button(text="💳 Пополнить баланс", callback_data="replenish_balance")
    builder.button(text="📱 Аккаунты", callback_data="accounts_menu")
    builder.button(text="📝 Шаблоны", callback_data="templates_menu")
    builder.button(text="🚀 Рассылки", callback_data="campaigns_menu")
    builder.button(text="🌐 Яндекс", callback_data="yandex_menu")
    builder.button(text="ℹ️ Информация", callback_data="info")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.button(text="📢 Наш канал", url="https://t.me/GRSspamnovosti")
    builder.adjust(2, 2, 3, 2, 1)
    return builder.as_markup()

def cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Отмена", callback_data="main_menu")
    return builder.as_markup()

async def check_subscription(user_id: int) -> bool:
    """Проверяет, активна ли подписка у пользователя (админы всегда имеют доступ)"""
    if user_id in ADMIN_IDS:
        return True
    try:
        sub = await get_subscription(user_id)
        if sub["status"] == "active" and sub["expires_at"]:
            expires = datetime.fromisoformat(sub["expires_at"])
            if expires > datetime.now():
                return True
            else:
                await set_subscription(user_id, "inactive")
                return False
    except:
        pass
    return False

# ---------- Обработчики ----------
@router.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery):
    """Показывает профиль пользователя"""
    # Проверка блокировки
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    user_id = callback.from_user.id
    try:
        user = await get_user(user_id)
        balance = await get_balance(user_id)
        sub = await get_subscription(user_id)

        if user and 'registered_at' in user and user['registered_at']:
            reg_date = datetime.fromisoformat(user['registered_at']).strftime("%d.%m.%Y %H:%M")
        else:
            reg_date = "неизвестно"

        if user_id in ADMIN_IDS:
            text = (
                f"👑 <b>Профиль администратора</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"📅 Регистрация: {reg_date}\n"
                f"💰 Баланс: {balance} USDT\n"
                f"👥 Подписка: бессрочно"
            )
        else:
            if sub["status"] == "active" and sub["expires_at"]:
                expires = datetime.fromisoformat(sub["expires_at"]).strftime("%d.%m.%Y %H:%M")
                text = (
                    f"👤 <b>Твой профиль</b>\n\n"
                    f"🆔 ID: {user_id}\n"
                    f"📅 Регистрация: {reg_date}\n"
                    f"💰 Баланс: {balance} USDT\n"
                    f"✅ Подписка активна до {expires}"
                )
            else:
                text = (
                    f"👤 <b>Твой профиль</b>\n\n"
                    f"🆔 ID: {user_id}\n"
                    f"📅 Регистрация: {reg_date}\n"
                    f"💰 Баланс: {balance} USDT\n"
                    f"❌ Подписка неактивна"
                )
    except Exception as e:
        text = f"👤 Профиль\n\n🆔 ID: {user_id}\n❌ Ошибка: {e}"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "buy_subscription")
async def buy_subscription_callback(callback: types.CallbackQuery, state: FSMContext):
    """Выбор тарифа подписки"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for key, tariff in SUBSCRIPTION_TARIFFS.items():
        builder.button(text=f"{tariff['label']} — {tariff['price']}$", callback_data=f"tariff_{key}")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "🔥 <b>Выбери тариф подписки</b> (оплата в USDT):",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PaymentState.choosing_tariff)
    await callback.answer()

@router.callback_query(PaymentState.choosing_tariff, F.data.startswith("tariff_"))
async def tariff_chosen(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбранного тарифа"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    tariff_key = callback.data.split("_")[1]
    tariff = SUBSCRIPTION_TARIFFS.get(tariff_key)
    if not tariff:
        await callback.message.edit_text("❌ Ошибка выбора тарифа.")
        await state.clear()
        return
    await state.update_data(tariff=tariff_key, price_usd=tariff["price"], days=tariff["days"])

    balance = await get_balance(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    if balance >= tariff["price"]:
        builder.button(text="💳 Оплатить с баланса", callback_data="pay_with_balance")
    if CRYPTO_OK:
        builder.button(text="💰 CryptoBot (USDT)", callback_data="method_cryptobot")
    builder.button(text="🚀 Xrocket", callback_data="method_xrocket")
    builder.button(text="◀️ Назад", callback_data="buy_subscription")
    builder.adjust(1)
    info = f"Тариф: {tariff['label']}\nСумма: {tariff['price']} USDT"
    if balance < tariff["price"]:
        info += f"\n\n⚠️ На балансе недостаточно средств ({balance} USDT)."
    await callback.message.edit_text(info, reply_markup=builder.as_markup())
    await state.set_state(PaymentState.choosing_method)
    await callback.answer()

@router.callback_query(PaymentState.choosing_method, F.data == "pay_with_balance")
async def pay_with_balance(callback: types.CallbackQuery, state: FSMContext):
    """Оплата подписки с внутреннего баланса"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    data = await state.get_data()
    price = data["price_usd"]
    days = data["days"]
    tariff = data["tariff"]
    user_id = callback.from_user.id

    balance = await get_balance(user_id)
    if balance < price:
        await callback.answer("❌ Недостаточно средств на балансе.", show_alert=True)
        return

    await update_balance(user_id, -price)
    await add_transaction(user_id, -price, "subscription_purchase", f"Тариф {tariff}")

    expires_at = datetime.now() + timedelta(days=days)
    await set_subscription(user_id, "active", expires_at.isoformat(), "balance")
    # Логирование (если есть функция log_action, добавьте её)
    # log_action(user_id, "subscription_purchased", f"{price} USDT, {days} дней, с баланса")
    await callback.message.edit_text("✅ Подписка успешно активирована за счёт баланса!")
    await state.clear()
    await main_menu_callback(callback)

@router.callback_query(PaymentState.choosing_method, F.data == "method_cryptobot")
async def pay_with_cryptobot(callback: types.CallbackQuery, state: FSMContext):
    """Создание счёта в CryptoBot"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    if not CRYPTO_OK:
        await callback.message.edit_text("❌ CryptoBot временно недоступен. Попробуйте позже или оплатите с баланса.")
        await state.clear()
        await callback.answer()
        return

    data = await state.get_data()
    price = data["price_usd"]
    days = data["days"]
    tariff = data["tariff"]
    user_id = callback.from_user.id

    try:
        # Предполагаем, что create_crypto_invoice асинхронная
        invoice_id, pay_url = await create_crypto_invoice(price, f"Подписка {tariff} user {user_id}")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании счёта: {e}")
        await state.clear()
        return

    await add_invoice(invoice_id, user_id, int(price*100), "cryptobot")
    await state.update_data(invoice_id=invoice_id, method="cryptobot", days=days)
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Перейти к оплате", url=pay_url)
    builder.button(text="✅ Я оплатил", callback_data="check_payment")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    await callback.message.edit_text(
        f"✅ Счёт создан!\n\n🔗 Ссылка для оплаты:\n{pay_url}\n\nПосле оплаты нажми «✅ Я оплатил».",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PaymentState.waiting_for_payment)
    await callback.answer()

@router.callback_query(PaymentState.waiting_for_payment, F.data == "check_payment")
async def check_payment(callback: types.CallbackQuery, state: FSMContext):
    """Проверка статуса оплаты CryptoBot"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    data = await state.get_data()
    invoice_id = data["invoice_id"]
    method = data["method"]
    price = data["price_usd"]
    days = data["days"]
    user_id = callback.from_user.id
    try:
        status = await check_crypto_invoice(invoice_id)
        if status == "paid":
            expires_at = datetime.now() + timedelta(days=days)
            await set_subscription(user_id, "active", expires_at.isoformat(), method)
            await update_invoice_status(invoice_id, "paid")
            # Бонус 5% на баланс
            bonus = round(price * 0.05, 2)
            await update_balance(user_id, bonus)
            await add_transaction(user_id, bonus, "subscription_bonus", f"Бонус за подписку")
            # log_action(user_id, "subscription_purchased", f"{price} USDT, {days} дней, {method}, бонус {bonus}")
            await callback.message.edit_text("✅ Подписка успешно активирована! Бонус зачислен на баланс.")
            await state.clear()
            await main_menu_callback(callback)
        else:
            await callback.answer("⏳ Платёж ещё не завершён.", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка при проверке: {e}", show_alert=True)

@router.callback_query(PaymentState.choosing_method, F.data == "method_xrocket")
async def pay_with_xrocket(callback: types.CallbackQuery, state: FSMContext):
    """Заглушка для Xrocket"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    await callback.message.edit_text("❌ Оплата через Xrocket временно недоступна.")
    await state.clear()

# ---------- Пополнение баланса ----------
@router.callback_query(F.data == "replenish_balance")
async def replenish_balance_callback(callback: types.CallbackQuery, state: FSMContext):
    """Начало пополнения баланса"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    await callback.message.edit_text(
        "💵 <b>Пополнение баланса</b>\n\nВведи сумму в USDT (например, 10):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(PaymentState.replenish_amount)
    await callback.answer()

@router.message(PaymentState.replenish_amount)
async def replenish_amount_entered(message: types.Message, state: FSMContext):
    """Получение суммы пополнения"""
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введи положительное число (например, 10).", reply_markup=cancel_keyboard())
        return
    await state.update_data(amount=amount)
    builder = InlineKeyboardBuilder()
    if CRYPTO_OK:
        builder.button(text="💰 CryptoBot (USDT)", callback_data="replenish_cryptobot")
    builder.button(text="🚀 Xrocket", callback_data="replenish_xrocket")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await message.answer(f"Сумма: {amount} USDT\nВыбери способ оплаты:", reply_markup=builder.as_markup())
    await state.set_state(PaymentState.replenish_method)

@router.callback_query(PaymentState.replenish_method, F.data.startswith("replenish_"))
async def replenish_choose_method(callback: types.CallbackQuery, state: FSMContext):
    """Выбор метода пополнения"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    method = callback.data.split("_")[1]
    data = await state.get_data()
    amount = data["amount"]
    user_id = callback.from_user.id

    if method == "cryptobot":
        if not CRYPTO_OK:
            await callback.message.edit_text("❌ CryptoBot временно недоступен.")
            await state.clear()
            return
        try:
            invoice_id, pay_url = await create_crypto_invoice(amount, f"Пополнение баланса user {user_id}")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка при создании счёта: {e}")
            await state.clear()
            return
    else:  # xrocket
        invoice_id = f"xr_{user_id}_{amount}"
        pay_url = "https://t.me/Xrocket_bot"

    await add_invoice(invoice_id, user_id, int(amount*100), method)
    await state.update_data(invoice_id=invoice_id, method=method)
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Перейти к оплате", url=pay_url)
    builder.button(text="✅ Я оплатил", callback_data="check_replenish")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    await callback.message.edit_text(
        f"✅ Счёт на пополнение создан!\n\n🔗 Ссылка для оплаты:\n{pay_url}\n\nПосле оплаты нажми «✅ Я оплатил».",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PaymentState.replenish_payment)
    await callback.answer()

@router.callback_query(PaymentState.replenish_payment, F.data == "check_replenish")
async def check_replenish(callback: types.CallbackQuery, state: FSMContext):
    """Проверка оплаты пополнения"""
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    data = await state.get_data()
    invoice_id = data["invoice_id"]
    method = data["method"]
    amount = data["amount"]
    user_id = callback.from_user.id
    try:
        if method == "cryptobot":
            status = await check_crypto_invoice(invoice_id)
        else:
            # Для Xrocket всегда считаем оплаченным (тест)
            status = "paid"
        if status == "paid":
            await update_balance(user_id, amount)
            await add_transaction(user_id, amount, "replenish", f"Пополнение через {method}")
            await update_invoice_status(invoice_id, "paid")
            # log_action(user_id, "balance_replenished", f"{amount} USDT, {method}")
            await callback.message.edit_text(f"✅ Баланс успешно пополнен на {amount} USDT!")
            await state.clear()
            await main_menu_callback(callback)
        else:
            await callback.answer("⏳ Платёж ещё не завершён.", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка при проверке: {e}", show_alert=True)

# ---------- Заглушки для остальных меню ----------
@router.callback_query(F.data == "templates_menu")
async def templates_menu_callback(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "❌ Нужна подписка.",
            reply_markup=InlineKeyboardBuilder().button(text="💰 Купить подписку", callback_data="buy_subscription").as_markup()
        )
        await callback.answer()
        return
    await callback.message.edit_text("📝 Управление шаблонами (в разработке)", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "campaigns_menu")
async def campaigns_menu_callback(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "❌ Нужна подписка.",
            reply_markup=InlineKeyboardBuilder().button(text="💰 Купить подписку", callback_data="buy_subscription").as_markup()
        )
        await callback.answer()
        return
    await callback.message.edit_text("🚀 Рассылки (в разработке)", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "yandex_menu")
async def yandex_menu_callback(callback: types.CallbackQuery):
    if not await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "❌ Нужна подписка.",
            reply_markup=InlineKeyboardBuilder().button(text="💰 Купить подписку", callback_data="buy_subscription").as_markup()
        )
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Создать лендинг", callback_data="yandex_create_landing")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "🌐 Яндекс.Лендинги",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "info")
async def info_callback(callback: types.CallbackQuery):
    text = (
        "🔥 <b>Самый крутой бот для автоматизации</b>\n\n"
        "✨ <b>Возможности:</b>\n"
        "• Массовые рассылки в Telegram, VK, MAX\n"
        "• Создание стильных лендингов с фото\n"
        "• Гибкие тарифы и оплата через CryptoBot\n"
        "• Внутренний баланс и бонусы\n"
        "• Поддержка 24/7\n\n"
        "👑 <b>Администратор:</b> @GRSmanager"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "support")
async def support_callback(callback: types.CallbackQuery):
    text = (
        "📞 <b>Связь с поддержкой</b>\n\n"
        "По всем вопросам пиши:\n"
        "@GRSmanager\n\n"
        "Ответим в ближайшее время!"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 <b>Главное меню</b>\nВыбери действие:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await main_menu_callback(callback)