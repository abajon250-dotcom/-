from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import add_template, get_templates, get_template, is_user_blocked
from handlers.common import get_nav_keyboard
from logger import log_action

router = Router()

class TemplateState(StatesGroup):
    name = State()
    platform = State()
    text = State()
    media = State()  # пока не используется

@router.callback_query(F.data == "templates_menu")
async def templates_menu_callback(callback: types.CallbackQuery):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Создать шаблон", callback_data="create_template")
    builder.button(text="📋 Мои шаблоны", callback_data="list_templates")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    await callback.message.edit_text(
        "📝 Управление шаблонами:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "create_template")
async def create_template_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введи название шаблона:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(TemplateState.name)

@router.message(TemplateState.name)
async def template_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название не может быть пустым.")
        return
    await state.update_data(name=name)
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 MAX", callback_data="tpl_platform_max")
    builder.button(text="✈️ Telegram", callback_data="tpl_platform_telegram")
    builder.button(text="📘 VK", callback_data="tpl_platform_vk")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(2)
    await message.answer("Выбери платформу:", reply_markup=builder.as_markup())
    await state.set_state(TemplateState.platform)

@router.callback_query(F.data.startswith("tpl_platform_"), TemplateState.platform)
async def template_platform(callback: types.CallbackQuery, state: FSMContext):
    platform = callback.data.replace("tpl_platform_", "")
    await state.update_data(platform=platform)
    await callback.message.edit_text(
        "Введи текст сообщения (можно использовать эмодзи):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(TemplateState.text)

@router.message(TemplateState.text)
async def template_text(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("❌ Текст не может быть пустым.")
        return
    await state.update_data(text=text)
    data = await state.get_data()
    await add_template(message.from_user.id, data["name"], data["platform"], text)
    log_action(message.from_user.id, "create_template", data["name"])
    await message.answer("✅ Шаблон создан!")
    await state.clear()
    from handlers.start import cmd_start
    await cmd_start(message)

@router.callback_query(F.data == "list_templates")
async def list_templates(callback: types.CallbackQuery):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    templates = await get_templates(user_id=callback.from_user.id)
    if not templates:
        await callback.message.edit_text(
            "📋 У вас пока нет сохранённых шаблонов.",
            reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="templates_menu").as_markup()
        )
        await callback.answer()
        return
    text = "📋 Ваши шаблоны:\n\n"
    for tpl in templates:
        text += f"🆔 {tpl['id']}: {tpl['name']} ({tpl['platform']})\n{tpl['text'][:50]}...\n\n"
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="templates_menu")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()