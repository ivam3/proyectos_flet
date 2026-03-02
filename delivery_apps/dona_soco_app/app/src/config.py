import os

# Configuración Global - Cargada desde variables de entorno
APP_NAME = os.getenv("APP_NAME", "Antojitos Doña Soco")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Antojitos Doña Soco")

# Identificador único para multi-tenencia
TENANT_ID = os.getenv("TENANT_ID", "dona_soco")

# URL de la API
API_URL = os.getenv("API_URL")

# Seguridad de la API (Sin valor por defecto para obligar configuración en Railway)
API_KEY = os.getenv("API_SECRET_KEY")

HEADERS = {
    "X-API-KEY": API_KEY,
    "X-Tenant-ID": TENANT_ID
}

# URL base para imágenes
IMAGES_URL = f"{API_URL}/static/uploads/{TENANT_ID}"
