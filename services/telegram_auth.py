import os
import time
import shutil
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    FloodWaitError,
    PhoneNumberInvalidError,
    PhoneCodeExpiredError,
)
from config import TG_API_ID, TG_API_HASH

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class TelegramAuth:
    def __init__(self, phone: str):
        self.phone = phone
        self.api_id = TG_API_ID
        self.api_hash = TG_API_HASH
        session_name = self._get_session_name()
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        self.phone_code_hash = None

    def _get_session_name(self):
        permanent = os.path.join(SESSIONS_DIR, self.phone)
        temp = os.path.join(SESSIONS_DIR, f'temp_{self.phone}')
        if os.path.exists(permanent + '.session'):
            return permanent
        return temp

    async def send_code(self):
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                result = await self.client.send_code_request(self.phone)
                self.phone_code_hash = result.phone_code_hash
                print(f"📤 Код отправлен. phone_code_hash={self.phone_code_hash}")
            else:
                raise Exception("Аккаунт уже авторизован")
        except FloodWaitError as e:
            wait_time = e.seconds
            print(f"⏳ FloodWait: нужно подождать {wait_time} сек")
            raise Exception(f"Слишком много попыток. Подождите {wait_time} секунд.")
        except PhoneNumberInvalidError:
            print("❌ Неверный формат номера")
            raise Exception("Неверный номер. Проверьте формат (например, +79001234567).")
        except Exception as e:
            print(f"❌ Ошибка отправки кода: {e}")
            raise

    async def check_code(self, code: str):
        try:
            await self.client.sign_in(self.phone, code, phone_code_hash=self.phone_code_hash)
            return True
        except SessionPasswordNeededError:
            return "2fa_required"
        except PhoneCodeExpiredError:
            raise Exception("Код подтверждения истёк. Запросите новый код.")
        except Exception as e:
            raise e

    async def check_2fa(self, password: str):
        try:
            await self.client.sign_in(password=password)
        except Exception as e:
            raise e

    def get_credentials(self):
        self.client.disconnect()
        time.sleep(0.5)
        temp_session = os.path.join(SESSIONS_DIR, f'temp_{self.phone}.session')
        final_session = os.path.join(SESSIONS_DIR, f'{self.phone}.session')
        if os.path.exists(temp_session):
            try:
                os.replace(temp_session, final_session)
                print(f"✅ Сессия переименована: {final_session}")
            except OSError as e:
                print(f"⚠️ Не удалось переименовать: {e}. Пробуем копировать и удалить.")
                try:
                    shutil.copy2(temp_session, final_session)
                    os.remove(temp_session)
                    print(f"✅ Сессия скопирована: {final_session}")
                except Exception as copy_err:
                    print(f"❌ Ошибка копирования: {copy_err}")
        return {
            "phone": self.phone,
            "session_file": final_session if os.path.exists(final_session) else temp_session,
            "api_id": self.api_id,
            "api_hash": self.api_hash
        }