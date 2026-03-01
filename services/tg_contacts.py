from telethon import TelegramClient
import logging

logger = logging.getLogger(__name__)

async def get_tg_stats(session_file, api_id, api_hash):
    """
    Возвращает статистику по аккаунту Telegram:
    - dialogs: количество диалогов
    - contacts: количество контактов
    """
    client = TelegramClient(session_file, api_id, api_hash)
    await client.connect()
    try:
        dialogs = await client.get_dialogs()
        contacts = await client.get_contacts()
        return {
            'dialogs': len(dialogs),
            'contacts': len(contacts)
        }
    except Exception as e:
        logger.exception("Ошибка при получении статистики Telegram")
        return None
    finally:
        await client.disconnect()