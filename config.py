import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

TG_API_ID = int(os.getenv("TG_API_ID", 0))
TG_API_HASH = os.getenv("TG_API_HASH")
if not TG_API_ID or not TG_API_HASH:
    raise ValueError("TG_API_ID и TG_API_HASH обязательны")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")  # но вы используете aiosqlite, это не обязательно

# VK Group Token (если используется)
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")

# GitHub Token (для деплоя лендинга)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Яндекс (если используется)
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")

# Прокси для VK (и Telegram, если нужно)
PROXY_URL = os.getenv("PROXY_URL")  # например: http://user:pass@ip:port
if PROXY_URL:
    PROXY_CONFIG = {
        'http': PROXY_URL,
        'https': PROXY_URL
    }
else:
    PROXY_CONFIG = None