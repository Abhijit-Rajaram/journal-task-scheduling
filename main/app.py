from fastapi import FastAPI
from datetime import datetime
# from main.celery_worker import send_scheduled_email

app = FastAPI()


@app.get("/")
def main():
    return {"status": "FastApi running"}

# @app.post("/schedule_email/")
# async def schedule_email(subject: str, body: str, to_email: str, schedule_time: datetime):
#     delay = (schedule_time - datetime.now()).total_seconds()

#     if delay < 0:
#         return {"error": "Time must be in the future"}

#     send_scheduled_email.apply_async(
#         (subject, body, to_email),
#         countdown=delay
#     )

#     return {"message": f"Email scheduled for {schedule_time}"}
