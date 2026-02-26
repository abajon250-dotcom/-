import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Список администраторов (ID Telegram)
ADMIN_IDS = []
admin_str = os.getenv("ADMIN_IDS", "")
if admin_str:
    for part in admin_str.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))

# Данные для Яндекс.Директ (если используются)
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_LOGIN = os.getenv("YANDEX_LOGIN")

# Пути для лендингов
LANDING_STORAGE_PATH = os.getenv("LANDING_STORAGE_PATH", "landings")
LANDING_BASE_URL = os.getenv("LANDING_BASE_URL", "http://localhost/landings/")

# Данные для ADB (MAX)
ADB_PATH = os.getenv("ADB_PATH", "adb")
MAX_PACKAGE = os.getenv("MAX_PACKAGE")
MAX_ACTIVITY = os.getenv("MAX_ACTIVITY")

# Telegram API для авторизации пользователей
TG_API_ID = int(os.getenv("TG_API_ID", 0))
TG_API_HASH = os.getenv("TG_API_HASH", "")

# Токены платёжных систем
CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")