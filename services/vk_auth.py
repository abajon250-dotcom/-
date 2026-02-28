import vk_api
import logging
import pickle
import base64
from vk_api.exceptions import ApiError, VkApiError

logger = logging.getLogger(__name__)

class VkAuth:
    def __init__(self, login: str):
        self.login = login
        self.vk_session = None
        self._twofa_code = None

    async def send_code(self):
        self.vk_session = vk_api.VkApi(login=self.login)
        try:
            self.vk_session.auth(token_only=True)
            logger.info(f"Уже авторизован для {self.login}")
            return True
        except vk_api.exceptions.TwoFactorError:
            logger.info(f"Требуется код для {self.login}")
            return False
        except vk_api.exceptions.BadPassword:
            logger.info(f"Требуется пароль/код для {self.login}")
            return False
        except Exception as e:
            logger.exception("Ошибка при инициализации VK")
            raise

    async def check_code(self, code: str):
        if not self.vk_session:
            self.vk_session = vk_api.VkApi(login=self.login)
        self._twofa_code = code
        try:
            self.vk_session.auth(token_only=True)
            return True
        except vk_api.exceptions.TwoFactorError:
            return "2fa_required"
        except vk_api.exceptions.BadPassword:
            raise Exception("Неверный код или пароль.")
        except Exception as e:
            raise e

    async def check_2fa(self, password: str):
        # Для VK двухфакторка обычно уже обработана в check_code
        pass

    def get_credentials(self):
        token = self.vk_session.token.get('access_token') if self.vk_session.token else None
        cookies = pickle.dumps(self.vk_session.http.cookies)
        # Преобразуем байты в строку base64
        cookies_b64 = base64.b64encode(cookies).decode('ascii')
        return {
            'login': self.login,
            'token': token,
            'cookies': cookies_b64,  # теперь строка, а не bytes
        }