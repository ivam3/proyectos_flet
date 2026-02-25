# Configuración Global de la Aplicación
# Cambia el valor de estas variables para personalizar la marca (White Label)

import os

APP_NAME = "Antojitos Doña Soco DEV"
COMPANY_NAME = "Antojitos Doña Soco" # Usado en reportes y encabezados

# Identificador único para multi-tenencia
TENANT_ID = os.getenv("TENANT_ID", "dona_soco")

# URL de la API, cambiar si se usa localmente
API_URL = os.getenv(
        "API_URL", "https://delivery-apps-api-dev.up.railway.app"
        )

# Seguridad de la API
API_KEY = os.getenv("API_SECRET_KEY", "ads2026_Ivam3byCinderella")
HEADERS = {
    "X-API-KEY": API_KEY,
    "X-Tenant-ID": TENANT_ID
}

# URL base para imágenes (aislamiento por tenant)
IMAGES_URL = f"{API_URL}/static/uploads/{TENANT_ID}"
