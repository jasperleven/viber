# Деплой Viber Bot на Hetzner

## 1. Подключись к серверу по SSH
ssh root@167.233.96.7

## 2. Создай папку и скопируй файлы
mkdir -p /opt/viber_bot
cd /opt/viber_bot

## 3. Скопируй все файлы проекта в /opt/viber_bot/
# (main.py, config.py, viber.py, database.py, handlers.py, scheduler.py, messages.py, requirements.txt)

## 4. Создай виртуальное окружение и установи зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## 5. Скопируй systemd сервис
cp viber_bot.service /etc/systemd/system/

## 6. Запусти сервис
systemctl daemon-reload
systemctl enable viber_bot
systemctl start viber_bot

## 7. Проверь статус
systemctl status viber_bot

## 8. Проверь логи
tail -f /var/log/viber_bot.log

## 9. Проверь что сервис отвечает
curl http://localhost:8001/health
