import os
import vk_api
import logging
import asyncio
from vk_api.exceptions import ApiError, VkApiError

logger = logging.getLogger(__name__)

SESSIONS_DIR = "sessions/vk"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class VkAuth:
    def __init__(self, login: str):
        self.login = login
        safe_login = login.replace('+', '').replace('@', '_').replace('.', '_')
        self.config_path = os.path.join(SESSIONS_DIR, f"{safe_login}.json")
        self.vk_session = None
        self._twofa_code = None

    async def send_code(self):
        def _init_and_try_auth():
            vk = vk_api.VkApi(
                login=self.login,
                config_filename=self.config_path,
                auth_handler=self._auth_handler_sync
            )
            try:
                vk.auth(token_only=True)
                return vk, True
            except vk_api.exceptions.TwoFactorError:
                return vk, False
            except vk_api.exceptions.BadPassword:
                return vk, False
            except Exception as e:
                logger.exception("Ошибка при предварительной авторизации VK")
                raise

        loop = asyncio.get_event_loop()
        self.vk_session, result = await loop.run_in_executor(None, _init_and_try_auth)
        return result

    def _auth_handler_sync(self):
        if self._twofa_code:
            return self._twofa_code, True
        raise vk_api.exceptions.TwoFactorError("2FA required")

    async def check_code(self, code: str):
        self._twofa_code = code
        if not self.vk_session:
            await self.send_code()

        def _auth_with_code():
            try:
                self.vk_session.auth(token_only=True)
                return True
            except vk_api.exceptions.TwoFactorError:
                return "2fa_required"
            except vk_api.exceptions.BadPassword:
                raise Exception("Неверный код или пароль.")
            except Exception as e:
                raise e

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _auth_with_code)

    async def check_2fa(self, password: str):
        self._twofa_code = password
        if not self.vk_session:
            await self.send_code()

        def _auth_with_password():
            try:
                self.vk_session.auth(token_only=True)
            except Exception as e:
                raise e

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _auth_with_password)

    def get_credentials(self):
        return {
            'phone': self.login,               # для совместимости с вашей БД (поле phone)
            'login': self.login,                # если нужно отдельно
            'session_file': self.config_path,   # путь к файлу сессии
        }