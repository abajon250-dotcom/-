import requests
from config import CRYPTO_PAY_TOKEN

API_URL = "https://pay.crypt.bot/api"

def create_invoice(amount_usd: float, description: str = "Подписка"):
    """
    Создаёт счёт в Crypto Pay на сумму amount_usd (в USDT).
    Возвращает (invoice_id, pay_url).
    """
    url = f"{API_URL}/createInvoice"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "asset": "USDT",
        "amount": str(amount_usd),
        "description": description,
        "paid_btn_name": "openBot",
        "paid_btn_url": "https://t.me/sjkgsjdfshdjbot",  # замените на своего бота
        "allow_comments": False,
        "allow_anonymous": False
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if data.get("ok"):
        return data["result"]["invoice_id"], data["result"]["pay_url"]
    else:
        raise Exception(f"CryptoPay error: {data}")

def check_invoice(invoice_id: str):
    """
    Проверяет статус счёта по invoice_id.
    Возвращает статус (paid, active, expired) или None.
    """
    url = f"{API_URL}/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    params = {"invoice_ids": invoice_id}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if data.get("ok") and data["result"]["items"]:
        return data["result"]["items"][0]["status"]
    return None