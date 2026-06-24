import logging
import requests
from config import STAGE_CONTRACT_SIGNED, STAGE_DELIVERY, STAGE_WAITING_DOCS, AMOCRM_DOMAIN, AMOCRM_TOKEN
from database import upsert_deal, set_contract_signed, set_delivery_notified, set_docs_stage
from viber import send_viber
from messages import msg_contract_signed, msg_delivery, msg_waiting_docs


def get_contact_by_deal(deal_id: str):
    """Получить телефон и имя контакта по ID сделки через AmoCRM API"""
    headers = {
        "Authorization": f"Bearer {AMOCRM_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # Шаг 1: получить сделку с контактами
        deal_url = f"https://{AMOCRM_DOMAIN}/api/v4/leads/{deal_id}?with=contacts"
        deal_resp = requests.get(deal_url, headers=headers, timeout=10)
        logging.info(f"Deal API response [{deal_resp.status_code}]: {deal_resp.text[:300]}")

        if deal_resp.status_code != 200:
            logging.error(f"Failed to get deal {deal_id}: {deal_resp.status_code}")
            return None, None

        deal_data = deal_resp.json()

        # Шаг 2: получить ID первого контакта
        contacts = deal_data.get("_embedded", {}).get("contacts", [])
        if not contacts:
            logging.warning(f"No contacts found for deal {deal_id}")
            return None, None

        contact_id = contacts[0]["id"]

        # Шаг 3: получить данные контакта
        contact_url = f"https://{AMOCRM_DOMAIN}/api/v4/contacts/{contact_id}"
        contact_resp = requests.get(contact_url, headers=headers, timeout=10)
        logging.info(f"Contact API response [{contact_resp.status_code}]: {contact_resp.text[:300]}")

        if contact_resp.status_code != 200:
            logging.error(f"Failed to get contact {contact_id}: {contact_resp.status_code}")
            return None, None

        contact_data = contact_resp.json()

        full_name = contact_data.get("name", "Клиент")
        first_name = contact_data.get("first_name", "").strip()
        # Если first_name пустой — берём второе слово из full_name (имя после фамилии)
        if not first_name:
            parts = full_name.split()
            first_name = parts[1] if len(parts) > 1 else parts[0] if parts else "Клиент"
        phone = None

        # Ищем телефон в custom_fields_values
        for field in contact_data.get("custom_fields_values", []) or []:
            if field.get("field_code") == "PHONE":
                values = field.get("values", [])
                if values:
                    phone = values[0].get("value")
                    break

        logging.info(f"Got contact for deal {deal_id}: name={first_name}, phone={phone}")
        return first_name, phone

    except Exception as e:
        logging.error(f"Error getting contact for deal {deal_id}: {e}", exc_info=True)
        return None, None


async def handle_webhook(data: dict):
    """Handle incoming webhook from AmoCRM"""
    try:
        logging.info(f"Processing webhook data: {data}")

        deal_id = None
        stage_id = None

        # Парсим формат AmoCRM вебхука (leads[update] и leads[status])
        for key, value in data.items():
            if "[id]" in key and ("leads[update][0]" in key or "leads[status][0]" in key):
                deal_id = str(value)
            elif "[status_id]" in key and ("leads[update][0]" in key or "leads[status][0]" in key):
                stage_id = str(value)

        if not deal_id:
            deal_id = (data.get("leads[update][0][id]") or
                      data.get("leads[status][0][id]") or
                      data.get("id"))
        if not stage_id:
            stage_id = str(data.get("leads[update][0][status_id]") or
                          data.get("leads[status][0][status_id]") or
                          data.get("status_id", ""))

        logging.info(f"Parsed: deal_id={deal_id}, stage_id={stage_id}")

        if not deal_id or not stage_id:
            logging.warning("Missing deal_id or stage_id, skipping")
            return

        # Берём имя и телефон из AmoCRM API
        first_name, phone = get_contact_by_deal(deal_id)

        if not phone:
            logging.warning(f"No phone found for deal {deal_id}, skipping")
            return

        # Сохраняем в БД
        upsert_deal(deal_id, phone, first_name, stage_id)

        # Обрабатываем стадию
        if stage_id == STAGE_CONTRACT_SIGNED:
            logging.info(f"Deal {deal_id}: Contract signed stage")
            set_contract_signed(deal_id)
            message = msg_contract_signed(first_name)
            send_viber(phone, message)

        elif stage_id == STAGE_DELIVERY:
            logging.info(f"Deal {deal_id}: Delivery stage")
            set_delivery_notified(deal_id)
            message = msg_delivery(first_name)
            send_viber(phone, message)

        elif stage_id == STAGE_WAITING_DOCS:
            logging.info(f"Deal {deal_id}: Waiting docs stage")
            set_docs_stage(deal_id)
            message = msg_waiting_docs(first_name)
            send_viber(phone, message)

        else:
            logging.info(f"Deal {deal_id}: Stage {stage_id} not handled")

    except Exception as e:
        logging.error(f"Error handling webhook: {e}", exc_info=True)
