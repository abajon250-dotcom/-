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

YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_LOGIN = os.getenv("YANDEX_LOGIN")

LANDING_STORAGE_PATH = os.getenv("LANDING_STORAGE_PATH", "landings")
LANDING_BASE_URL = os.getenv("LANDING_BASE_URL", "http://localhost/landings/")

ADB_PATH = os.getenv("ADB_PATH", "adb")
MAX_PACKAGE = os.getenv("MAX_PACKAGE")
MAX_ACTIVITY = os.getenv("MAX_ACTIVITY")

TG_API_ID = int(os.getenv("TG_API_ID", 0))
TG_API_HASH = os.getenv("TG_API_HASH", "")

CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")

# Добавляем эту строку
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")