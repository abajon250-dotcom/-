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
        logger.info(f"VkAuth.send_code для {self.login}")

        def _init():
            vk = vk_api.VkApi(
                login=self.login,
                config_filename=self.config_path,
                auth_handler=self._auth_handler_sync
            )
            return vk

        loop = asyncio.get_event_loop()
        self.vk_session = await loop.run_in_executor(None, _init)

        def _try_token():
            try:
                self.vk_session.auth(token_only=True)
                return True
            except vk_api.exceptions.TwoFactorError:
                return False
            except vk_api.exceptions.BadPassword:
                return False
            except Exception as e:
                logger.exception("Ошибка при auth(token_only=True)")
                raise

        result = await loop.run_in_executor(None, _try_token)
        if result:
            logger.info(f"Уже авторизован по токену для {self.login}")
            return True
        else:
            logger.info(f"Требуется код для {self.login}")
            return False

    def _auth_handler_sync(self):
        if self._twofa_code:
            return self._twofa_code, True
        raise vk_api.exceptions.TwoFactorError("2FA required")

    async def check_code(self, code: str):
        logger.info(f"VkAuth.check_code для {self.login}")
        self._twofa_code = code
        if not self.vk_session:
            await self.send_code()

        def _auth():
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
        return await loop.run_in_executor(None, _auth)

    async def check_2fa(self, password: str):
        logger.info(f"VkAuth.check_2fa для {self.login}")
        self._twofa_code = password
        if not self.vk_session:
            await self.send_code()

        def _auth():
            try:
                self.vk_session.auth(token_only=True)
            except Exception as e:
                raise e

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _auth)

    def get_credentials(self):
        return {
            'phone': self.login,
            'login': self.login,
            'session_file': self.config_path,
        }

    def get_token(self):
        if self.vk_session and self.vk_session.token:
            return self.vk_session.token.get('access_token')
        return None