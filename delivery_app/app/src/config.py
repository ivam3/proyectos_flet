# Configuración Global de la Aplicación
# Cambia el valor de estas variables para personalizar la marca (White Label)

import os

APP_NAME = "Delivery APP"
COMPANY_NAME = "Ivam3byCinderella" # Usado en reportes y encabezados

# URL de la API, cambiar si se usa localmente
API_URL = os.getenv(
        "API_URL", "http://localhost:8000" # Cambia a la URL de tu API si no es local
        )

# Seguridad de la API
API_KEY = "IbyC2026_Ivam3byCinderella" # Cambia esta clave por una segura y única para tu aplicación
HEADERS = {"X-API-KEY": API_KEY}
