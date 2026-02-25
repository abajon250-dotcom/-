import vk_api
from vk_api import VkApi
from vk_api.exceptions import ApiError
import threading

class VkAuth:
    def __init__(self, phone):
        self.phone = phone
        self.vk_session = VkApi(phone)
        self.vk = self.vk_session.get_api()
        self.code_needed = threading.Event()
        self.password_needed = threading.Event()
        self.auth_result = None
        self.code = None
        self.password = None

    async def send_code(self):
        def auth_thread():
            try:
                self.vk_session.auth(reauth=True)
                self.auth_result = True
            except vk_api.AuthError as e:
                if "2fa" in str(e) or "code" in str(e).lower():
                    self.code_needed.set()
                else:
                    self.auth_result = e
        thread = threading.Thread(target=auth_thread)
        thread.start()
        self.code_needed.wait(timeout=30)
        if not self.code_needed.is_set():
            raise Exception("Таймаут при запросе кода")
        # Код отправлен на телефон

    async def check_code(self, code):
        self.code = code
        def continue_auth():
            try:
                self.vk_session.auth(reauth=True, code=self.code)
                self.auth_result = True
            except vk_api.AuthError as e:
                if "2fa" in str(e):
                    self.password_needed.set()
                else:
                    self.auth_result = e
        thread = threading.Thread(target=continue_auth)
        thread.start()
        self.password_needed.wait(timeout=30)
        if self.password_needed.is_set():
            return "2fa_required"
        if self.auth_result is True:
            return True
        else:
            raise Exception(self.auth_result)

    async def check_2fa(self, password):
        self.password = password
        def final_auth():
            try:
                self.vk_session.auth(reauth=True, code=self.code, password=self.password)
                self.auth_result = True
            except Exception as e:
                self.auth_result = e
        thread = threading.Thread(target=final_auth)
        thread.start()
        thread.join(timeout=30)
        if self.auth_result is True:
            return True
        else:
            raise Exception(self.auth_result)

    def get_credentials(self):
        token = self.vk_session.token['access_token']
        return {"token": token}