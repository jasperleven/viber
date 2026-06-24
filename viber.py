import re
import requests
import logging
from config import SMSTRAFFIC_LOGIN, SMSTRAFFIC_PASSWORD, SMSTRAFFIC_URL, SENDER_NAME, ROUTE

def send_viber(phone: str, message: str) -> bool:
    """Send Viber message via SMS Traffic API, fallback to SMS"""
    try:
        # Оставляем только цифры, убираем всё лишнее: +, пробелы, тире, скобки
        phone_clean = re.sub(r'[^\d]', '', phone)
        
        params = {
            "login": SMSTRAFFIC_LOGIN,
            "password": SMSTRAFFIC_PASSWORD,
            "phones": phone_clean,
            "message": message,
            "originator": SENDER_NAME,
            "route": ROUTE,
            "rus": "5",
        }
        
        response = requests.post(SMSTRAFFIC_URL, data=params, timeout=10)
        logging.info(f"SMS Traffic response: {response.text}")
        
        if "<result>OK</result>" in response.text:
            logging.info(f"Message sent successfully to {phone_clean}")
            return True
        else:
            logging.error(f"Failed to send message to {phone_clean}: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending message to {phone}: {e}")
        return False
