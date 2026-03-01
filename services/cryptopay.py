# services/cryptopay.py
# Заглушка для CryptoBot, чтобы кнопка появилась

def create_invoice(amount: float, description: str = ""):
    """
    Заглушка: возвращает тестовый invoice_id и ссылку
    """
    # Можно использовать любой invoice_id и ссылку
    invoice_id = f"test_{amount}_{hash(description)}"
    pay_url = "https://t.me/CryptoBot?start=test"
    return invoice_id, pay_url

def check_invoice(invoice_id: str):
    """
    Заглушка: всегда возвращает "paid", чтобы при нажатии "Я оплатил" срабатывало
    """
    return "paid"