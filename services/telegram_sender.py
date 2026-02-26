import os
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
import logging

async def send_telegram_messages(session_file: str, api_id: int, api_hash: str, contacts: list, message_text: str, delay_min: int, delay_max: int):
    """
    Отправляет сообщения списку контактов через указанную сессию Telegram.
    contacts – список строк (username, phone или user_id).
    """
    client = TelegramClient(session_file, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        logging.error(f"Сессия {session_file} не авторизована")
        return

    for contact in contacts:
        try:
            entity = await client.get_input_entity(contact)
            await client.send_message(entity, message_text)
            logging.info(f"Сообщение отправлено {contact}")
        except FloodWaitError as e:
            logging.warning(f"Flood wait {e.seconds} сек, ждём")
            await asyncio.sleep(e.seconds)
            # можно попробовать повторить позже
        except Exception as e:
            logging.error(f"Ошибка отправки {contact}: {e}")

        # Задержка между сообщениями
        delay = delay_min if delay_min == delay_max else (delay_min + delay_max) // 2
        await asyncio.sleep(delay)

    await client.disconnect()