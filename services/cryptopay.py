import logging
from aiocryptopay import AioCryptoPay
from config import CRYPTOBOT_TOKEN

logger = logging.getLogger(__name__)

_crypto_instance = None

async def get_crypto():
    global _crypto_instance
    if _crypto_instance is None:
        # По умолчанию MainNet
        _crypto_instance = AioCryptoPay(token=CRYPTOBOT_TOKEN)
    return _crypto_instance

async def create_invoice(amount: float, description: str = "") -> tuple[str, str]:
    crypto = await get_crypto()
    try:
        invoice = await crypto.create_invoice(
            asset='USDT',
            amount=amount,
            description=description
        )
        logger.info(f"Создан инвойс {invoice.invoice_id} на {amount} USDT")
        return str(invoice.invoice_id), invoice.pay_url
    except Exception as e:
        logger.exception("Ошибка создания инвойса CryptoPay")
        raise Exception(f"Ошибка при создании счёта: {e}")

async def check_invoice(invoice_id: str) -> str:
    crypto = await get_crypto()
    try:
        # invoice_id должен быть числом для API
        invoices = await crypto.get_invoices(invoice_ids=int(invoice_id))
        if invoices:
            return invoices[0].status
        return "not_found"
    except Exception as e:
        logger.exception(f"Ошибка проверки инвойса {invoice_id}")
        raise Exception(f"Ошибка при проверке: {e}")