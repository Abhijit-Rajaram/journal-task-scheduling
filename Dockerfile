FROM python:3.11-slim

WORKDIR /app

COPY main/ /app/main
COPY main/requirements.txt .
COPY .env .env

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main.app:app", "--host", "0.0.0.0", "--port", "8000"]
