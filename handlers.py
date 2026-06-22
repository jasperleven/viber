import logging
from config import STAGE_CONTRACT_SIGNED, STAGE_DELIVERY, STAGE_WAITING_DOCS
from database import upsert_deal, set_contract_signed, set_delivery_notified, set_docs_stage
from viber import send_viber
from messages import msg_contract_signed, msg_delivery, msg_waiting_docs

async def handle_webhook(data: dict):
    """Handle incoming webhook from AmoCRM"""
    try:
        logging.info(f"Processing webhook data: {data}")
        
        # AmoCRM sends data in format: leads[update][0][field]
        # Extract deal data
        deal_id = None
        stage_id = None
        phone = None
        name = None
        
        # Parse AmoCRM webhook format
        for key, value in data.items():
            if "leads[update][0][id]" in key or key == "leads[update][0][id]":
                deal_id = str(value)
            elif "leads[update][0][status_id]" in key:
                stage_id = str(value)
            elif "leads[update][0][name]" in key:
                name = value
        
        # Try to get contact name and phone
        for key, value in data.items():
            if "contacts[update][0][name]" in key or "contacts[add][0][name]" in key:
                if not name:
                    name = value
            if "phone" in key.lower() and value:
                phone = value

        # Also check common AmoCRM webhook formats
        if not deal_id:
            deal_id = data.get("leads[update][0][id]") or data.get("id")
        if not stage_id:
            stage_id = str(data.get("leads[update][0][status_id]") or data.get("status_id", ""))
        if not name:
            name = data.get("leads[update][0][name]") or data.get("name", "Клиент")
        if not phone:
            # Search for phone in all keys
            for key, value in data.items():
                if "phone" in key.lower() and value and str(value).strip():
                    phone = str(value).strip()
                    break

        logging.info(f"Parsed: deal_id={deal_id}, stage_id={stage_id}, name={name}, phone={phone}")

        if not deal_id or not stage_id:
            logging.warning("Missing deal_id or stage_id, skipping")
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
