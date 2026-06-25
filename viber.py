import re
import requests
import logging
from config import SMSTRAFFIC_LOGIN, SMSTRAFFIC_PASSWORD, SMSTRAFFIC_URL, SENDER_NAME, ROUTE

def send_viber(phone: str, viber_message: str, sms_message: str) -> bool:
    """Send Viber message via SMS Traffic API, fallback to SMS with separate text"""
    try:
        # Оставляем только цифры
        phone_clean = re.sub(r'\D', '', phone)
        
        params = {
            "login": SMSTRAFFIC_LOGIN,
            "password": SMSTRAFFIC_PASSWORD,
            "phones": phone_clean,
            "message": viber_message,
            "sms_text": sms_message,
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
