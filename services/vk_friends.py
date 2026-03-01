import vk_api
import logging
from vk_api.exceptions import ApiError

logger = logging.getLogger(__name__)

def get_friends_stats(token):
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        friends = vk.friends.get(count=0)
        return {'total': friends['count']}
    except ApiError as e:
        logger.exception("Ошибка при получении друзей VK")
        return None