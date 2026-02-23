# Configuración Global de la Aplicación
# Cambia el valor de estas variables para personalizar la marca (White Label)

import os

APP_NAME = "Antojitos Doña Soco DEV"
COMPANY_NAME = "Antojitos Doña Soco" # Usado en reportes y encabezados

# URL de la API, cambiar si se usa localmente
API_URL = os.getenv(
        "API_URL", "https://dona-soco-api-dev.up.railway.app"
        )

# Seguridad de la API
API_KEY = "ads2026_Ivam3byCinderella"
HEADERS = {"X-API-KEY": API_KEY}
