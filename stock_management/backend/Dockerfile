FROM python:3.13-slim

WORKDIR /app

# Copiar requerimientos desde la raíz del proyecto
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY . .

# Comando para iniciar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
