import logging
from urllib.parse import unquote_plus
from config import STAGE_CONTRACT_SIGNED, STAGE_DELIVERY, STAGE_WAITING_DOCS
from database import upsert_deal, set_contract_signed, set_delivery_notified, set_docs_stage
from viber import send_viber
from messages import msg_contract_signed, msg_delivery, msg_waiting_docs

async def handle_webhook(data: dict):
    """Handle incoming webhook from AmoCRM"""
    try:
        logging.info(f"Processing webhook data: {data}")

        deal_id = None
        stage_id = None
        phone = None
        name = "Клиент"

        # AmoCRM sends leads[status][0][id] format
        for key, value in data.items():
            k = key.strip()
            v = str(value).strip() if value else ""

            if k == "leads[status][0][id]" or k == "leads[update][0][id]" or k == "leads[add][0][id]":
                deal_id = v
            elif k == "leads[status][0][status_id]" or k == "leads[update][0][status_id]":
                stage_id = v
            elif "name" in k and "account" not in k and "subdomain" not in k:
                if v:
                    name = v
            elif "phone" in k.lower() and v:
                phone = v

        logging.info(f"Parsed: deal_id={deal_id}, stage_id={stage_id}, name={name}, phone={phone}")

        if not deal_id:
            logging.warning("Missing deal_id, skipping")
            return

        if not stage_id:
            logging.warning("Missing stage_id, skipping")
            return

        if not phone:
            logging.warning(f"No phone found for deal {deal_id}, skipping")
            return

        # Clean name - take first word
        first_name = name.split()[0] if name else "Клиент"

        # Save/update deal in DB
        upsert_deal(deal_id, phone, first_name, stage_id)

        # Handle stage
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
