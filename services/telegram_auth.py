import os
import logging
from telethon import TelegramClient, errors
from config import TG_API_ID, TG_API_HASH

logger = logging.getLogger(__name__)

SESSIONS_DIR = "sessions/telegram"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class TelegramAuth:
    def __init__(self, phone: str):
        self.phone = phone
        self.api_id = TG_API_ID
        self.api_hash = TG_API_HASH
        safe_phone = phone.replace('+', '')
        self.session_path = os.path.join(SESSIONS_DIR, safe_phone)
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        self.phone_code_hash = None

    async def send_code(self):
        await self.client.connect()
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            if me and me.phone == self.phone:
                logger.info(f"Уже авторизован для {self.phone}")
                return True
            else:
                await self.client.log_out()
        try:
            result = await self.client.send_code_request(self.phone)
            self.phone_code_hash = result.phone_code_hash
            logger.info(f"Код отправлен на {self.phone}")
            return False
        except errors.FloodWaitError as e:
            raise Exception(f"Слишком много попыток. Подождите {e.seconds} сек.")
        except errors.PhoneNumberInvalidError:
            raise Exception("Неверный формат номера")
        except Exception as e:
            logger.exception("Ошибка отправки кода")
            raise

    async def check_code(self, code: str):
        try:
            await self.client.sign_in(self.phone, code, phone_code_hash=self.phone_code_hash)
            return True
        except errors.SessionPasswordNeededError:
            return "2fa_required"
        except errors.PhoneCodeExpiredError:
            raise Exception("Код истёк. Запросите новый.")
        except errors.PhoneCodeInvalidError:
            raise Exception("Неверный код.")
        except Exception as e:
            raise e

    async def check_2fa(self, password: str):
        try:
            await self.client.sign_in(password=password)
        except errors.PasswordHashInvalidError:
            raise Exception("Неверный пароль 2FA")
        except Exception as e:
            raise e

    def get_credentials(self):
        self.client.disconnect()
        return {
            "phone": self.phone,
            "session_file": f"{self.session_path}.session",
            "api_id": self.api_id,
            "api_hash": self.api_hash
        }