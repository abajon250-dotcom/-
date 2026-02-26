import asyncio
import csv
import os
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import (
    get_user_accounts_by_platform, get_templates, get_template, add_campaign, is_user_blocked,
    get_account  # нужен для получения деталей аккаунта
)
from services.telegram_sender import send_telegram_messages
from handlers.common import get_nav_keyboard
from config import LANDING_STORAGE_PATH  # для временных файлов

router = Router()

class CampaignState(StatesGroup):
    platform = State()
    account_id = State()
    template_id = State()
    text = State()          # если без шаблона
    contacts = State()
    confirm_contacts = State()
    delay_min = State()
    delay_max = State()

@router.callback_query(F.data == "campaigns_menu")
async def campaigns_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📱 MAX", callback_data="camp_platform_max")
    builder.button(text="✈️ Telegram", callback_data="camp_platform_telegram")
    builder.button(text="📘 VK", callback_data="camp_platform_vk")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(2, 1)
    await callback.message.edit_text(
        "🚀 Выбери платформу для рассылки:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CampaignState.platform)

@router.callback_query(F.data.startswith("camp_platform_"), CampaignState.platform)
async def campaign_platform(callback: types.CallbackQuery, state: FSMContext):
    platform = callback.data.replace("camp_platform_", "")
    await state.update_data(platform=platform)

    # Показываем аккаунты пользователя для этой платформы
    accounts = await get_user_accounts_by_platform(callback.from_user.id, platform)
    if not accounts:
        await callback.message.edit_text(
            f"❌ У вас нет добавленных аккаунтов для {platform}. Сначала добавьте аккаунт.",
            reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="campaigns_menu").as_markup()
        )
        await state.clear()
        return

    builder = InlineKeyboardBuilder()
    for acc in accounts:
        label = acc['credentials'].get('phone', f"ID {acc['id']}")
        builder.button(text=label, callback_data=f"camp_acc_{acc['id']}")
    builder.button(text="◀️ Назад", callback_data="campaigns_menu")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(2)
    await callback.message.edit_text(
        "Выбери аккаунт для рассылки:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CampaignState.account_id)

@router.callback_query(F.data.startswith("camp_acc_"), CampaignState.account_id)
async def campaign_account(callback: types.CallbackQuery, state: FSMContext):
    acc_id = int(callback.data.replace("camp_acc_", ""))
    await state.update_data(account_id=acc_id)

    # Показываем шаблоны пользователя для этой платформы
    data = await state.get_data()
    platform = data["platform"]
    templates = await get_templates(platform=platform, user_id=callback.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Без шаблона (ввести текст)", callback_data="camp_tpl_none")
    for tpl in templates:
        builder.button(text=tpl['name'], callback_data=f"camp_tpl_{tpl['id']}")
    builder.button(text="◀️ Назад", callback_data="campaigns_menu")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(2)
    await callback.message.edit_text(
        "Выбери шаблон или введи текст вручную:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CampaignState.template_id)

@router.callback_query(F.data.startswith("camp_tpl_"), CampaignState.template_id)
async def campaign_template_chosen(callback: types.CallbackQuery, state: FSMContext):
    tpl_id = callback.data.replace("camp_tpl_", "")
    if tpl_id == "none":
        await state.update_data(template_id=None)
        await callback.message.edit_text(
            "Введи текст сообщения для рассылки:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        await state.set_state(CampaignState.text)
    else:
        tpl_id = int(tpl_id)
        tpl = await get_template(tpl_id)
        await state.update_data(template_id=tpl_id, text=tpl["text"])
        await callback.message.edit_text(
            "Теперь загрузи список контактов (csv с одним столбцем) или введи их через запятую:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        await state.set_state(CampaignState.contacts)

@router.message(CampaignState.text)
async def campaign_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым.")
        return
    await state.update_data(text=text)
    await message.answer(
        "Теперь загрузи список контактов (csv с одним столбцем) или введи их через запятую:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(CampaignState.contacts)

@router.message(CampaignState.contacts)
async def campaign_contacts(message: types.Message, state: FSMContext, bot: Bot):
    contacts = []
    if message.document:
        # Скачиваем CSV
        try:
            file = await bot.get_file(message.document.file_id)
            file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
            await bot.download_file(file.file_path, file_path)
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and row[0].strip():
                        contacts.append(row[0].strip())
            os.remove(file_path)
        except Exception as e:
            await message.answer(f"❌ Ошибка при чтении файла: {e}")
            return
    else:
        contacts = [c.strip() for c in message.text.split(",") if c.strip()]

    if not contacts:
        await message.answer("❌ Список контактов пуст.")
        return

    await state.update_data(contacts=contacts)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Далее", callback_data="camp_contacts_ok")
    builder.button(text="🔄 Загрузить заново", callback_data="camp_contacts_again")
    builder.button(text="◀️ Назад к шаблону", callback_data="back_to_template")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(1)
    await message.answer(
        f"📋 Загружено контактов: {len(contacts)}\nВсё верно?",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CampaignState.confirm_contacts)

@router.callback_query(F.data == "camp_contacts_again", CampaignState.confirm_contacts)
async def contacts_again(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Загрузи список контактов заново:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(CampaignState.contacts)

@router.callback_query(F.data == "back_to_template", CampaignState.confirm_contacts)
async def back_to_template(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    templates = await get_templates(platform=data["platform"], user_id=callback.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Без шаблона (ввести текст)", callback_data="camp_tpl_none")
    for tpl in templates:
        builder.button(text=tpl['name'], callback_data=f"camp_tpl_{tpl['id']}")
    builder.button(text="◀️ Назад", callback_data="campaigns_menu")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(2)
    await callback.message.edit_text(
        "Выбери шаблон или введи текст вручную:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CampaignState.template_id)

@router.callback_query(F.data == "camp_contacts_ok", CampaignState.confirm_contacts)
async def contacts_ok(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введи минимальную задержку между сообщениями (секунд):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(CampaignState.delay_min)

@router.message(CampaignState.delay_min)
async def campaign_delay_min(message: types.Message, state: FSMContext):
    try:
        delay_min = int(message.text)
        if delay_min < 1:
            raise ValueError
    except:
        await message.answer("❌ Введи целое положительное число.")
        return
    await state.update_data(delay_min=delay_min)
    await message.answer(
        "Введи максимальную задержку (секунд):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(CampaignState.delay_max)

@router.message(CampaignState.delay_max)
async def campaign_delay_max(message: types.Message, state: FSMContext):
    try:
        delay_max = int(message.text)
        if delay_max < 1:
            raise ValueError
    except:
        await message.answer("❌ Введи целое положительное число.")
        return

    data = await state.get_data()
    platform = data["platform"]
    account_id = data["account_id"]
    text = data["text"]
    contacts = data["contacts"]
    delay_min = data["delay_min"]
    delay_max = delay_max

    # Сохраняем кампанию в БД (опционально)
    await add_campaign(
        user_id=message.from_user.id,
        platform=platform,
        account_id=account_id,
        template_id=data.get("template_id"),
        contacts=contacts,
        delay_min=delay_min,
        delay_max=delay_max
    )

    await message.answer(
        f"🚀 Запускаю рассылку по {platform} на {len(contacts)} контактов...\n"
        f"Задержка: {delay_min}-{delay_max} сек."
    )

    # Запускаем в фоне
    asyncio.create_task(
        run_campaign_task(
            platform, account_id, text, contacts,
            delay_min, delay_max, message
        )
    )
    await state.clear()

async def run_campaign_task(platform, account_id, text, contacts, delay_min, delay_max, notify_msg):
    try:
        account = await get_account(account_id)  # функция из database
        if not account:
            await notify_msg.answer("❌ Аккаунт не найден")
            return

        if platform == "telegram":
            # Получаем данные для отправки из credentials
            creds = account["credentials"]
            session_file = creds.get("session_file")
            api_id = creds.get("api_id")
            api_hash = creds.get("api_hash")
            if not all([session_file, api_id, api_hash]):
                await notify_msg.answer("❌ Недостаточно данных для отправки через Telegram")
                return
            await send_telegram_messages(session_file, api_id, api_hash, contacts, text, delay_min, delay_max)
            await notify_msg.answer("✅ Рассылка через Telegram завершена!")
        elif platform == "vk":
            # Заглушка
            await notify_msg.answer("📘 Рассылки через VK пока в разработке.")
        elif platform == "max":
            # Заглушка
            await notify_msg.answer("📱 Рассылки через MAX пока в разработке.")
        else:
            await notify_msg.answer("❌ Неизвестная платформа")
    except Exception as e:
        await notify_msg.answer(f"❌ Ошибка при рассылке: {e}")