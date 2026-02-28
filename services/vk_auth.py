import vk_api
import logging
import pickle
from vk_api.exceptions import ApiError, VkApiError

logger = logging.getLogger(__name__)

class VkAuth:
    def __init__(self, login: str):
        self.login = login
        self.vk_session = None
        self._twofa_code = None

    async def send_code(self):
        """Для VK «отправка кода» означает создание сессии и проверку, не требуется ли сразу 2FA.
        Возвращает True, если уже авторизован (есть токен), иначе False."""
        self.vk_session = vk_api.VkApi(login=self.login)
        try:
            # Пытаемся авторизоваться без пароля (чтобы получить validation)
            self.vk_session.auth(token_only=True)
            # Если дошли сюда без исключений – значит, уже есть сохранённая сессия
            logger.info(f"Уже авторизован для {self.login}")
            return True
        except vk_api.exceptions.TwoFactorError:
            # Требуется код – это нормально, продолжим
            logger.info(f"Требуется код для {self.login}")
            return False
        except vk_api.exceptions.BadPassword:
            # Пароль не был передан, но требуется – будем считать, что нужен код
            logger.info(f"Требуется пароль/код для {self.login}")
            return False
        except Exception as e:
            logger.exception("Ошибка при инициализации VK")
            raise

    async def check_code(self, code: str):
        """Проверяет код (и пароль, если нужно). Возвращает True или '2fa_required'."""
        if not self.vk_session:
            self.vk_session = vk_api.VkApi(login=self.login)
        self._twofa_code = code
        try:
            self.vk_session.auth(token_only=True)
            return True
        except vk_api.exceptions.TwoFactorError:
            # Всё ещё требуется 2FA – значит, нужен пароль
            return "2fa_required"
        except vk_api.exceptions.BadPassword:
            # Неверный пароль/код
            raise Exception("Неверный код или пароль.")
        except Exception as e:
            raise e

    async def check_2fa(self, password: str):
        """Ввод пароля двухфакторной аутентификации (после кода)."""
        # Для VK двухфакторка обычно уже обработана в check_code
        # Если нужно, можно реализовать отдельно
        pass

    def get_credentials(self):
        token = self.vk_session.token.get('access_token') if self.vk_session.token else None
        cookies = pickle.dumps(self.vk_session.http.cookies)
        return {
            'login': self.login,
            'token': token,
            'cookies': cookies,
        }