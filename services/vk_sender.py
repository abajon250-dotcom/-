import vk_api
import asyncio
import logging

async def send_vk_messages(token: str, contacts: list, message_text: str, delay_min: int, delay_max: int):
    """
    Отправляет сообщения списку контактов через VK API.
    contacts – список строк (user_id или screen_name).
    """
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    for contact in contacts:
        try:
            user_id = contact
            if not contact.isdigit():
                # Если это не число, пытаемся разрешить screen_name
                resolved = vk.utils.resolveScreenName(screen_name=contact)
                if resolved and resolved['type'] == 'user':
                    user_id = resolved['object_id']
                else:
                    logging.error(f"Не удалось разрешить screen_name {contact}")
                    continue
            # Отправляем сообщение
            vk.messages.send(user_id=int(user_id), message=message_text, random_id=0)
            logging.info(f"VK сообщение отправлено {contact}")
        except vk_api.exceptions.ApiError as e:
            logging.error(f"VK API ошибка для {contact}: {e}")
        except Exception as e:
            logging.error(f"Ошибка отправки VK {contact}: {e}")
        # Задержка
        delay = delay_min if delay_min == delay_max else (delay_min + delay_max) // 2
        await asyncio.sleep(delay)