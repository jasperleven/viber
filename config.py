import os
from pathlib import Path

# Секреты не хранятся в коде: они лежат в файле .env рядом с этим файлом
# (/opt/viber_bot/.env на сервере) или в переменных окружения сервиса.


def _load_env_file(path=Path(__file__).resolve().with_name(".env")):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Не задан {name}: добавь его в файл .env рядом с config.py")
    return value


_load_env_file()

# SMS Traffic credentials
SMSTRAFFIC_LOGIN = _required("SMSTRAFFIC_LOGIN")
SMSTRAFFIC_PASSWORD = _required("SMSTRAFFIC_PASSWORD")
SMSTRAFFIC_URL = "https://sds.smstraffic.by/smartdelivery-in/multi.php"

# AmoCRM settings
AMOCRM_DOMAIN = os.environ.get("AMOCRM_DOMAIN", "daangrah000.amocrm.ru")
AMOCRM_TOKEN = _required("AMOCRM_TOKEN")

# AmoCRM pipeline stage IDs
STAGE_CONTRACT_SIGNED = "69561406"   # Договор подписан
STAGE_DELIVERY = "85411634"          # Доставка товара
STAGE_WAITING_DOCS = "85398474"      # Ожидаем документы

# Message settings
COMPLAINT_PHONE = "+375 (29) 102-78-85"       # Артагед
CONDITIONS_URL = "https://technowave.by/of"   # Артагед

COMPLAINT_PHONE_SV = "+375 (44) 540-79-97"    # Синий ветер
CONDITIONS_URL_SV = "https://salesmarket.by/of"  # Синий ветер

SENDER_NAME = "texnowaveby"

# Viber route: сначала Viber 24 часа, потом SMS
ROUTE = "viber(86400)-sms"

# Weekly reminder interval in days
REMINDER_INTERVAL_DAYS = 7
