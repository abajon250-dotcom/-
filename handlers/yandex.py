import os
import subprocess
import requests
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.landing import generate_landing
from config import LANDING_STORAGE_PATH, LANDING_BASE_URL
from logger import log_action
from handlers.common import get_nav_keyboard
from database import is_user_blocked

router = Router()

class YandexState(StatesGroup):
    landing_name = State()
    template = State()
    title = State()
    description = State()
    button_text = State()
    offer_link = State()
    photo = State()

# Функция сокращения ссылок через clck.ru
def shorten_url(long_url):
    try:
        response = requests.get(f"https://clck.ru/--?url={long_url}", timeout=5)
        if response.status_code == 200:
            short = response.text.strip()
            if short.startswith("http"):
                return short
    except Exception as e:
        print(f"Ошибка сокращения ссылки: {e}")
    return long_url

def git_push(repo_path, commit_message):
    """
    Автоматический пуш лендингов на GitHub.
    При необходимости можно закомментировать, если на сервере нет Git.
    """
    try:
        os.chdir(repo_path)
        subprocess.run(["git", "add", "landings"], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        return True, "Успешно запушено"
    except subprocess.CalledProcessError as e:
        return False, str(e)

@router.callback_query(F.data == "yandex_menu")
async def yandex_menu(callback: types.CallbackQuery):
    if await is_user_blocked(callback.from_user.id):
        await callback.message.edit_text("🚫 Вы заблокированы.")
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Создать лендинг", callback_data="yandex_create_landing")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "🌐 Яндекс.Реклама:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "yandex_create_landing")
async def create_landing_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введи название лендинга (латиницей, без пробелов):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(YandexState.landing_name)

@router.message(YandexState.landing_name)
async def landing_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name or ' ' in name:
        await message.answer(
            "❌ Название должно быть без пробелов и не пустым. Попробуй ещё раз:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return
    await state.update_data(landing_name=name)

    builder = InlineKeyboardBuilder()
    builder.button(text="📰 Новости", callback_data="tpl_news")
    builder.button(text="🚗 ДТП", callback_data="tpl_accident")
    builder.button(text="🦠 Коронавирус", callback_data="tpl_covid")
    builder.button(text="🚔 ГИБДД ДТП", callback_data="tpl_gibdd")
    builder.button(text="📱 MAX Новости", callback_data="tpl_max")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(2, 2, 2)

    await message.answer(
        "Выбери тему лендинга:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(YandexState.template)

@router.callback_query(F.data.startswith("tpl_"), YandexState.template)
async def landing_template(callback: types.CallbackQuery, state: FSMContext):
    template = callback.data.replace("tpl_", "")
    await state.update_data(template=template)

    if template == "gibdd":
        default_image = "https://source.unsplash.com/featured/?accident,police"
    elif template == "accident":
        default_image = "https://source.unsplash.com/featured/?accident,car"
    elif template == "covid":
        default_image = "https://source.unsplash.com/featured/?covid,hospital"
    elif template == "max":
        default_image = "https://source.unsplash.com/featured/?smartphone,app"
    else:
        default_image = "https://source.unsplash.com/featured/?newspaper"

    await state.update_data(default_image=default_image)

    await callback.message.edit_text(
        "Введи заголовок лендинга:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(YandexState.title)

@router.message(YandexState.title)
async def landing_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer(
            "❌ Заголовок не может быть пустым. Введи снова:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return
    await state.update_data(title=title)
    await message.answer(
        "Введи описание:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(YandexState.description)

@router.message(YandexState.description)
async def landing_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if not desc:
        await message.answer(
            "❌ Описание не может быть пустым. Введи снова:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return
    await state.update_data(description=desc)
    await message.answer(
        "Введи текст кнопки:",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(YandexState.button_text)

@router.message(YandexState.button_text)
async def landing_button(message: types.Message, state: FSMContext):
    btn = message.text.strip()
    if not btn:
        await message.answer(
            "❌ Текст кнопки не может быть пустым. Введи снова:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return
    await state.update_data(button_text=btn)
    await message.answer(
        "Введи ссылку для кнопки (оффер):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(YandexState.offer_link)

@router.message(YandexState.offer_link)
async def landing_offer(message: types.Message, state: FSMContext):
    link = message.text.strip()
    if not link:
        await message.answer(
            "❌ Ссылка не может быть пустой. Введи снова:",
            reply_markup=get_nav_keyboard(show_cancel=True)
        )
        return
    await state.update_data(offer_link=link)

    # Запрашиваем фото
    await message.answer(
        "📸 Теперь отправь фотографию для лендинга (или напиши «пропустить» для фото по умолчанию):",
        reply_markup=get_nav_keyboard(show_cancel=True)
    )
    await state.set_state(YandexState.photo)

@router.message(YandexState.photo, F.photo)
async def landing_photo(message: types.Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    data = await state.get_data()
    landing_name = data["landing_name"]
    landing_dir = os.path.join(LANDING_STORAGE_PATH, landing_name)
    os.makedirs(landing_dir, exist_ok=True)
    photo_filename = "user_photo.jpg"
    photo_path = os.path.join(landing_dir, photo_filename)
    await bot.download_file(file.file_path, photo_path)
    await state.update_data(image_path=photo_filename)
    await finalize_landing(message, state)

@router.message(YandexState.photo, F.text.lower() == "пропустить")
async def skip_photo(message: types.Message, state: FSMContext):
    await state.update_data(image_path=None)
    await finalize_landing(message, state)

@router.message(YandexState.photo)
async def invalid_photo(message: types.Message):
    await message.answer("Пожалуйста, отправь фотографию или напиши «пропустить».")

async def finalize_landing(message: types.Message, state: FSMContext):
    data = await state.get_data()
    landing_name = data["landing_name"]
    template = data["template"]
    title = data["title"]
    description = data["description"]
    button_text = data["button_text"]
    offer_link = data["offer_link"]

    if data.get("image_path"):
        base = LANDING_BASE_URL.rstrip('/')
        image_url = f"{base}/{landing_name}/{data['image_path']}"
    else:
        image_url = data.get("default_image", "https://source.unsplash.com/featured/?news")

    try:
        url = generate_landing(
            name=landing_name,
            template_name=template,
            title=title,
            description=description,
            button_text=button_text,
            offer_link=offer_link,
            image_url=image_url,
            date="Сегодня",
            category="Срочные новости",
            views="1.2k",
            source="Lenta.ru"
        )
        log_action(message.from_user.id, "create_landing", landing_name)

        # Автопуш на GitHub (если Git установлен и настроен)
        repo_path = r"E:\БОТ2"  # замените на путь к корню вашего проекта на сервере, если нужно
        commit_msg = f"Добавлен лендинг {landing_name}"
        # Если на сервере нет Git, закомментируйте следующие строки:
        success, push_msg = git_push(repo_path, commit_msg)
        if success:
            await message.answer("✅ Лендинг создан и загружен на GitHub!")
        else:
            await message.answer(f"⚠️ Лендинг создан локально, но не запушен: {push_msg}")

        # Показываем обычную и короткую ссылки
        await message.answer(f"🌐 Обычная ссылка:\n{url}")
        short_url = shorten_url(url)
        await message.answer(f"🔗 Короткая ссылка:\n{short_url}")

    except Exception as e:
        await message.answer(f"❌ Ошибка при создании лендинга: {e}")
    await state.clear()
    await yandex_menu(message)