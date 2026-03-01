import logging
from aiocryptopay import AioCryptoPay
from config import CRYPTOBOT_TOKEN

logger = logging.getLogger(__name__)

_crypto = None

async def get_crypto():
    global _crypto
    if _crypto is None:
        _crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN)
    return _crypto

async def create_invoice(amount: float, description: str = ""):
    crypto = await get_crypto()
    invoice = await crypto.create_invoice(
        asset='USDT',
        amount=amount,
        description=description
    )
    logger.info(f"Invoice created: {invoice.invoice_id}")
    return str(invoice.invoice_id), invoice.pay_url

async def check_invoice(invoice_id: str):
    crypto = await get_crypto()
    invoices = await crypto.get_invoices(invoice_ids=int(invoice_id))
    if invoices:
        return invoices[0].status
    return "not_found"