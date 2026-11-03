from datetime import datetime, timedelta
import asyncio
from fastapi import FastAPI, Request
import requests

app = FastAPI()

AUTH_TOKEN = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyNDYwMzE0Iiwic2NwIjoib3BlbmlkIHByb2ZpbGUiLCJtc2giOiIzYzNkNGFiYS0wNjRjLTRmMjAtOThiZC00MDM0Y2MyYmUyMWEiLCJpc3MiOiJodHRwczpcL1wvYXV0aGVkdS5tb3NyZWcucnUiLCJncm91cHMiOnsiYWR1bHQiOjF9LCJzc28iOiIxMTg4Njg3NTQyIiwibmJmIjoxNzkzNjk2MzIyLCJhdGgiOiJlc2lhIiwicmxzIjoiezMyOlsxOToyOltdLDEzOTo0OltdLDE3NzoxNjpbXSwxODk6MTpbXSwyMTA6MTk6W10sNDY4OjQ0OltdLDU2OTo0ODpbXSw2MzA6NjY6W11dfSx7MTpbMzA6NDpbXV19IiwicmduIjoiNTAiLCJleHAiOjE3OTQ1NjAzMjIsImlhdCI6MTc5MzY5NjMyMiwianRpIjoiY2MxM2I2ODEtNGNkMy00Mjg3LTkzYjYtODE0Y2QzNDI4N2MwIn0.DKShrO9Vz5zR96UCGS2d7ukx-KQo1Jom4_psvaWS4qN9HOmbY4jDr8VVEt7mk4goz32gTwb7t_PKe5jCvfqz5fNlxoh1nZJr4h05n0kknK9LKCXbdIdS7tGZZ1cyS2uCglZH3udOPxP0-dfsP8zGPkbfrOyAAfMpGOXy5P4mbCHzynQ6c406tCF-a_YjwxvJk-ZBf6iwJQcLTj-Te8JoQY50D-H3tXXI0VRVNlyHu8XleEC7I4At-5bjC3OWbF7kKKGSqNKFfOUifui5p1Ix0pX_GCT6iUblthv9uzriIgsIj18qTibrBUafMReyfe8b1RM2JPvG9jEbiXuc3X812w"
PERSON_ID = "3c3d4aba-064c-4f20-98bd-4034cc2be21a"


def fetch_mesh(target_date: str) -> str:
    url = (
        f"https://authedu.mosreg.ru/api/profeducation/eventcalendar/v1/api/events"
        f"?person_ids={PERSON_ID}&begin_date={target_date}&end_date={target_date}"
        f"&expand=marks,homework,absence_reason_id,health_status,nonattendance_reason_id"
        f"&source_types=PLAN,EVENTS,CAFISHA,ORGANIZER"
    )

    headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 YaBrowser/26.10.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "profile-id": "1471174",
    "profile-type": "student",
    "x-mes-role": "student",
    "x-mes-subsystem": "familyspow",
    "Cookie": f"aupd_token={AUTH_TOKEN}; aupd_current_role=66:32; subsystem_id=66; active_student=1471174; obr_id=2460314;"
}
    # Жесткий таймаут 2.0 секунды, чтобы гарантированно успеть ответить Алисе
    res = requests.get(url, headers=headers, timeout=2.0)
    if res.status_code != 200:
        return f"Сервер дневника ответил ошибкой {res.status_code}. Проверь токен."

    data = res.json()
    events = (
        data.get("response", [])
        if isinstance(data, dict)
        else (data if isinstance(data, list) else [])
    )

    if not events:
        return "На завтра пар нет. Можно отдыхать!"

    pairs = []
    for item in events:
        start_time = item.get("start_at", "")
        if "T" in start_time:
            start_time = start_time.split("T")[1][:5]

        title = (
            item.get("title")
            or item.get("subject_name")
            or item.get("name")
            or "Пара"
        )
        room = item.get("room", "") or item.get("room_number", "")
        room_text = f", кабинет {room}" if room else ""
        pairs.append(
            f"В {start_time} — {title}{room_text}"
            if start_time
            else f"{title}{room_text}"
        )

    if not pairs:
        return "На завтра пар не запланировано."

    return f"Завтра пар: {len(pairs)}. " + ", ".join(pairs)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/")
async def webhook(request: Request):
    req_data = await request.json()
    moscow_now = datetime.utcnow() + timedelta(hours=3)
    tomorrow = (moscow_now + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        # Запускаем в отдельном пуле с лимитом времени
        speech = await asyncio.wait_for(
            asyncio.to_thread(fetch_mesh, tomorrow),
            timeout=2.4
        )
    except asyncio.TimeoutError:
        speech = "Дневник МЭШ слишком долго отвечает, не успеваю загрузить расписание."
    except Exception as e:
        speech = "Произошла ошибка при получении данных."

    return {
        "response": {"text": speech, "end_session": True},
        "version": req_data.get("version", "1.0"),
    }
