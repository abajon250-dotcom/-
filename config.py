import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = []
admin_str = os.getenv("ADMIN_IDS", "")
if admin_str:
    for part in admin_str.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))

# Токены для внешних сервисов
CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Telegram API для авторизации
TG_API_ID = int(os.getenv("TG_API_ID", 0))
TG_API_HASH = os.getenv("TG_API_HASH", "")

# Лендинги
LANDING_STORAGE_PATH = os.getenv("LANDING_STORAGE_PATH", "landings")
LANDING_BASE_URL = os.getenv("LANDING_BASE_URL", "http://localhost/landings/")

# Яндекс.Директ (если используется)
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_LOGIN = os.getenv("YANDEX_LOGIN")

# ADB (MAX)
ADB_PATH = os.getenv("ADB_PATH", "adb")
MAX_PACKAGE = os.getenv("MAX_PACKAGE")
MAX_ACTIVITY = os.getenv("MAX_ACTIVITY")