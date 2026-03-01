import os
from dotenv import load_dotenv

load_dotenv()

# Токен Telegram бота (обязательно)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

# Telegram API (для Telethon)
TG_API_ID = int(os.getenv("TG_API_ID", 0))
TG_API_HASH = os.getenv("TG_API_HASH")
if not TG_API_ID or not TG_API_HASH:
    raise ValueError("TG_API_ID и TG_API_HASH обязательны")

# Список администраторов (Telegram ID через запятую)
ADMIN_IDS = []
admin_str = os.getenv("ADMIN_IDS", "")
if admin_str:
    for part in admin_str.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))

# Токен для Crypto Pay (оплата подписок) – используется в payment.py
CRYPTOPAY_TOKEN = os.getenv("CRYPTOPAY_TOKEN")
# Для совместимости со старым именем (если в .env используется CRYPTO_PAY_TOKEN)
if not CRYPTOPAY_TOKEN:
    CRYPTOPAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")

# Токен для Xrocket (если используется)
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")

# Токен GitHub для загрузки лендингов
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Настройки лендингов
LANDING_STORAGE_PATH = os.getenv("LANDING_STORAGE_PATH", "landings")
LANDING_BASE_URL = os.getenv("LANDING_BASE_URL", "http://localhost/landings/")

# Данные для Яндекс.Директ (если используются)
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_LOGIN = os.getenv("YANDEX_LOGIN")

# Данные для ADB (MAX)
ADB_PATH = os.getenv("ADB_PATH", "adb")
MAX_PACKAGE = os.getenv("MAX_PACKAGE")
MAX_ACTIVITY = os.getenv("MAX_ACTIVITY")

# Прокси (для VK и Telegram, если нужно)
PROXY_URL = os.getenv("PROXY_URL")
if PROXY_URL:
    PROXY_CONFIG = {
        'http': PROXY_URL,
        'https': PROXY_URL
    }
else:
    PROXY_CONFIG = None

# Токены для других платёжных систем (если используются)