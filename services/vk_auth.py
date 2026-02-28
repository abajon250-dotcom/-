import os
import pickle
import vk_api
from vk_api import VkApi
from vk_api.exceptions import ApiError, AuthError

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class VkAuth:
    def __init__(self, phone: str):
        self.phone = phone
        self.session_file = os.path.join(SESSIONS_DIR, f"vk_{phone}.session")
        self.vk_session = None
        self.vk = None

    async def send_code(self):
        if os.path.exists(self.session_file):
            with open(self.session_file, 'rb') as f:
                token = pickle.load(f)
            self.vk_session = vk_api.VkApi(token=token)
            self.vk = self.vk_session.get_api()
            return True

        self.vk_session = vk_api.VkApi(login=self.phone)
        try:
            self.vk_session.auth()
        except AuthError as e:
            raise Exception("Требуется код подтверждения")
        except Exception as e:
            raise e

    async def check_code(self, code: str):
        try:
            # Передаём код как позиционный аргумент, не именованный
            self.vk_session.auth(code)
            token = self.vk_session.token['access_token']
            with open(self.session_file, 'wb') as f:
                pickle.dump(token, f)
            self.vk = self.vk_session.get_api()
            return True
        except AuthError as e:
            if "2fa" in str(e).lower() or "two" in str(e).lower():
                return "2fa_required"
            else:
                raise e
        except Exception as e:
            raise e

    async def check_2fa(self, password: str):
        # Для двухфакторки тоже передаём пароль как аргумент
        try:
            self.vk_session.auth(password)
            token = self.vk_session.token['access_token']
            with open(self.session_file, 'wb') as f:
                pickle.dump(token, f)
            self.vk = self.vk_session.get_api()
            return True
        except Exception as e:
            raise e

    def get_credentials(self):
        return {
            "phone": self.phone,
            "token": self.vk_session.token['access_token'],
            "session_file": self.session_file
        }