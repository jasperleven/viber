from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
import logging
from handlers import handle_webhook
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/viber_bot.log'),
        logging.StreamHandler()
    ]
)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    logging.info("Viber bot started")

@app.post("/webhook/amocrm")
async def webhook(request: Request):
    try:
        body = await request.body()
        logging.info(f"Webhook received: {body.decode('utf-8')}")
        
        form_data = await request.form()
        data = dict(form_data)
        
        await handle_webhook(data)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/oauth")
async def oauth(request: Request, code: str = None, state: str = None, error: str = None):
    """OAuth callback endpoint for AmoCRM integration"""
    logging.info(f"OAuth callback: code={code}, state={state}, error={error}")
    if code:
        return HTMLResponse(f"""
            <html><body>
            <h2>Интеграция успешно подключена!</h2>
            <p>Код авторизации получен. Скопируйте его и передайте администратору:</p>
            <b>{code}</b>
            </body></html>
        """)
    return HTMLResponse("<html><body><h2>OAuth endpoint работает</h2></body></html>")

@app.get("/health")
async def health():
    return {"status": "ok"}
