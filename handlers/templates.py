from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from database import add_template, get_templates, get_template
from keyboards import back_to_menu_keyboard, cancel_keyboard

router = Router()

class TemplateStates(StatesGroup):
    waiting_name = State()
    waiting_platform = State()
    waiting_content = State()

@router.callback_query(F.data == "templates_menu")
async def templates_menu(callback: CallbackQuery):
    templates = await get_templates(user_id=callback.from_user.id)
    text = "📋 **Ваши шаблоны**\n\n"
    if not templates:
        text += "У вас пока нет шаблонов."
    else:
        for t in templates:
            text += f"• {t['name']} ({t['platform']})\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать шаблон", callback_data="create_template")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "create_template")
async def create_template_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ Введите название шаблона:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(TemplateStates.waiting_name)
    await callback.answer()

@router.message(StateFilter(TemplateStates.waiting_name))
async def process_template_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer(
        "📱 Выберите платформу:\ntelegram / vk",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(TemplateStates.waiting_platform)

@router.message(StateFilter(TemplateStates.waiting_platform))
async def process_template_platform(message: Message, state: FSMContext):
    platform = message.text.strip().lower()
    if platform not in ('telegram', 'vk'):
        await message.answer("❌ Платформа должна быть 'telegram' или 'vk'. Попробуйте снова.")
        return
    await state.update_data(platform=platform)
    await message.answer(
        "📝 Введите текст шаблона (можно с эмодзи и Markdown):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(TemplateStates.waiting_content)

@router.message(StateFilter(TemplateStates.waiting_content))
async def process_template_content(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    platform = data['platform']
    content = message.text
    await add_template(message.from_user.id, name, platform, content)
    await message.answer(f"✅ Шаблон '{name}' сохранён!", reply_markup=back_to_menu_keyboard())
    await state.clear()