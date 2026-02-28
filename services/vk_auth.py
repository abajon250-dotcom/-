import os
import pickle
import vk_api
from vk_api import VkApi
from vk_api.exceptions import ApiError, AuthError
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
import asyncio

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class VkAuth:
    def __init__(self, phone: str):
        self.phone = phone
        self.session_file = os.path.join(SESSIONS_DIR, f"vk_{phone}.session")
        self.vk_session = None
        self.vk = None

    async def send_code(self):
        """
        Начинает процесс авторизации. Если есть сохранённая сессия – восстанавливает.
        Иначе выбрасывает исключение, сигнализирующее о необходимости кода.
        """
        # Проверяем наличие сохранённой сессии
        if os.path.exists(self.session_file):
            with open(self.session_file, 'rb') as f:
                token = pickle.load(f)
            self.vk_session = vk_api.VkApi(token=token)
            self.vk = self.vk_session.get_api()
            return True  # уже авторизован

        # Нет сессии – начинаем новую, которая запросит код
        self.vk_session = vk_api.VkApi(login=self.phone)
        try:
            self.vk_session.auth(token_only=True)
        except AuthError as e:
            # Здесь vk_api выбросит исключение с требованием кода
            # Мы его перехватим и передадим наружу, чтобы бот запросил код
            raise Exception("Требуется код подтверждения")
        except Exception as e:
            raise e

    async def check_code(self, code: str):
        """
        Вводит полученный код подтверждения.
        Если успешно – возвращает True.
        Если требуется двухфакторка – возвращает '2fa_required'.
        Если неверный код – выбрасывает исключение.
        """
        try:
            self.vk_session.auth(code=code)
            # Если дошли сюда – авторизация успешна
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
        """
        Ввод двухфакторного пароля (для VK это обычно код из приложения).
        """
        try:
            self.vk_session.auth(code=password)  # в VK двухфакторка передаётся как code?
            token = self.vk_session.token['access_token']
            with open(self.session_file, 'wb') as f:
                pickle.dump(token, f)
            self.vk = self.vk_session.get_api()
            return True
        except Exception as e:
            raise e

    def get_credentials(self):
        """
        Возвращает данные для сохранения в БД (токен и телефон).
        """
        return {
            "phone": self.phone,
            "token": self.vk_session.token['access_token'],
            "session_file": self.session_file
        }

    async def get_friends(self, mutual_only: bool = False):
        """
        Возвращает список друзей (user_id и имя).
        Если mutual_only=True – только взаимные подписчики.
        """
        if not self.vk:
            raise Exception("Не авторизован")
        try:
            friends = self.vk.friends.get(fields='first_name,last_name')
            items = friends['items']
            if mutual_only:
                # Взаимные подписчики – это те, у кого mutual=true
                items = [f for f in items if f.get('mutual', {}).get('mutual', False)]
            return items
        except Exception as e:
            raise e