from datetime import datetime, timedelta
from fastapi import FastAPI, Request
import requests

app = FastAPI()

FIREBASE_URL = "https://alicee-22bad-default-rtdb.firebaseio.com"

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/")
async def webhook(request: Request):
    req_data = await request.json()
    moscow_now = datetime.utcnow() + timedelta(hours=3)
    tomorrow = (moscow_now + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        res = requests.get(f"{FIREBASE_URL}/schedule/{tomorrow}.json", timeout=2.0)
        speech = res.json()
        if not speech:
            speech = "Расписание на завтра еще не загружено в облако."
    except Exception:
        speech = "Произошла ошибка при чтении облачной базы."

    return {
        "response": {"text": speech, "end_session": True},
        "version": req_data.get("version", "1.0"),
    }
