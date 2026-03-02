# 🚚 Delivery Apps Multi-tenant System

Una solución profesional, moderna y adaptable de **Software como Servicio (SaaS)** para servicios a domicilio. Diseñada originalmente para el giro restaurantero (Antojitos, Tortas, etc.), pero extensible a cualquier negocio como abarrotes, boutiques o farmacias.

Este ecosistema permite gestionar múltiples negocios (**tenants**) bajo un mismo motor de Backend, ofreciendo autonomía total a cada marca con su propio catálogo, configuración y gestión de pedidos.

---

## 🏗️ Arquitectura del Sistema

El proyecto está dividido en tres componentes principales:

1.  **Backend (API):** Construido con **FastAPI** y **PostgreSQL**. Centraliza la lógica de negocio, persistencia de datos, seguridad y sistema de redireccionamiento (acortador).
2.  **Frontend (App):** Aplicaciones multiplataforma (Web/APK) construidas con **Flet**. Experiencia de usuario fluida con soporte para SPA (Single Page Application).
3.  **Herramienta Admin (CLI):** Un potente sistema de línea de comandos (`db_admin.py`) para gestión masiva de datos, importación/exportación de respaldos JSON y mantenimiento.

---

## ✨ Características Principales

*   **Multi-tenancy:** Aislamiento de datos por `Tenant ID` en una única base de datos.
*   **Gestión de Menú Dinámica:** Soporte para platillos configurables (guisos, salsas, extras) y grupos de opciones ilimitados.
*   **Seguridad por Capas:** Comunicación protegida mediante `API_SECRET_KEY` y variables de entorno.
*   **Panel Administrativo:** Interfaz integrada en la app para control de pedidos en tiempo real, configuración de horarios y métodos de pago.
*   **Acortador Inteligente:** Sistema de redirección rápida (ej: `/apk`) gestionado desde la base de datos para facilitar descargas y promociones.
*   **Build Profesional:** Optimización de imágenes a formato **WebP** y motor de renderizado **CanvasKit**.

---

## 🚀 Guía de Instalación Local

### Requisitos Previos
*   Python 3.10 o superior.
*   Git.

### Pasos
1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/ivam3/proyectos_flet.git
    cd delivery_apps
    ```

2.  **Configurar el Backend:**
    ```bash
    cd backend
    cp .env.example .env
    # Edita .env con tu API_SECRET_KEY
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

3.  **Configurar el Frontend (Ejemplo Dona Soco):**
    ```bash
    cd dona_soco_app/app/src
    cp config.py.example config.py
    # Edita config.py con la URL de tu API local y tu API_SECRET_KEY
    cd ..
    pip install -r requirements.txt # Si existe, o instala flet
    flet run --web
    ```

---

## 🛠️ Herramienta Administrativa CLI

La herramienta `db_admin.py` es el corazón de la gestión técnica del sistema.

### Uso Básico
```bash
python db_admin.py [nombre_de_carpeta_del_negocio]
```

### Comandos Clave:
*   `ls`: Lista todos los platillos del catálogo.
*   `importar [archivo.json]`: Sincroniza datos masivamente respetando IDs y aislamiento por tenant.
*   `backup [nombre.json]`: Genera un respaldo completo del negocio actual.
*   `addlink [codigo] [url]`: Crea un enlace corto oficial (ej: `apk`).
*   `links`: Muestra todos los redireccionamientos activos.
*   `upload [ruta_imagen]`: Sube y convierte automáticamente imágenes a WebP en el servidor.

---

## 🌐 Despliegue en Producción (Railway)

Este proyecto está optimizado para **Railway** utilizando Docker.

1.  **Variables de Entorno Necesarias:**
    *   `API_SECRET_KEY`: La clave maestra compartida entre Backend y Frontends.
    *   `DATABASE_URL`: URL de conexión a PostgreSQL.
    *   `API_URL`: URL pública del servicio de Backend.
    *   `TENANT_ID`: Identificador único del negocio (ej: `dona_soco`).

2.  **CI/CD:**
    El sistema utiliza GitHub Actions (`.github/workflows/flet-web.yml`) para automatizar la construcción y el despliegue de los frontends cada vez que se detectan cambios en la rama principal.

---

## 📱 Compilación para Android (APK)

Para generar el instalador móvil:
```bash
cd dona_soco_app/app
flet build apk --verbose
```
*Nota: Requiere tener configurado el entorno de Flutter y Android SDK.*

---

## 📝 Licencia y Créditos
Proyecto desarrollado por **Ivam3byCinderella**. Todos los derechos reservados.
