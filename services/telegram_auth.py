import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from config import TG_API_ID, TG_API_HASH

class TelegramAuth:
    def __init__(self, phone):
        self.phone = phone
        self.api_id = TG_API_ID
        self.api_hash = TG_API_HASH
        self.client = TelegramClient(f'sessions/temp_{phone}', self.api_id, self.api_hash)
        self.phone_code_hash = None

    async def send_code(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            result = await self.client.send_code_request(self.phone)
            self.phone_code_hash = result.phone_code_hash
        else:
            raise Exception("Уже авторизован")

    async def check_code(self, code):
        try:
            await self.client.sign_in(self.phone, code, phone_code_hash=self.phone_code_hash)
            return True
        except SessionPasswordNeededError:
            return "2fa_required"
        except Exception as e:
            raise e

    async def check_2fa(self, password):
        try:
            await self.client.sign_in(password=password)
        except Exception as e:
            raise e

    def get_credentials(self):
        session_file = f"sessions/{self.phone}.session"
        self.client.disconnect()
        return {
            "phone": self.phone,
            "session_file": session_file,
            "api_id": self.api_id,
            "api_hash": self.api_hash
        }