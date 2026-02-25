import requests
from config import CRYPTO_PAY_TOKEN

def create_invoice(amount_usd, description):
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    payload = {
        "asset": "USDT",
        "amount": str(amount_usd),
        "description": description
    }
    r = requests.post(url, json=payload, headers=headers)
    data = r.json()
    if data.get("ok"):
        return data["result"]["invoice_id"], data["result"]["pay_url"]
    raise Exception(data)

def check_invoice(invoice_id):
    url = "https://pay.crypt.bot/api/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}
    params = {"invoice_ids": invoice_id}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    if data.get("ok") and data["result"]["items"]:
        return data["result"]["items"][0]["status"]
    return None