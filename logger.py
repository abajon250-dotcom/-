import logging

logging.basicConfig(
    filename='user_actions.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_action(user_id: int, action: str, details: str = ""):
    message = f"User {user_id}: {action}"
    if details:
        message += f" - {details}"
    logging.info(message)