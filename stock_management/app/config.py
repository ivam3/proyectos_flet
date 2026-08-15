import os

# Configuración Global
APP_NAME = os.getenv("APP_NAME", "Rik's Stock Management")
TENANT_ID = os.getenv("TENANT_ID", "stockman")

# URL de la API (Local por defecto)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Seguridad
API_KEY = os.getenv("API_SECRET_KEY", "")

HEADERS = {
    "X-API-KEY": API_KEY,
    "X-Tenant-ID": TENANT_ID
}
