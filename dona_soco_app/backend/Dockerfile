FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Copiar el folder web que ahora reside dentro de backend/
COPY web ./web

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
