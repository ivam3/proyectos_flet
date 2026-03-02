# 🚚 Delivery Apps Multi-tenant System

Una solución profesional, moderna y adaptable de **Software como Servicio (SaaS)** para servicios a domicilio. Diseñada originalmente para el giro restaurantero, pero extensible a cualquier modelo de negocio basado en catálogo y pedidos.

Este ecosistema permite gestionar múltiples marcas (**tenants**) bajo un mismo motor de Backend, ofreciendo autonomía total a cada marca con su propio catálogo, configuración y administración.

---

## 🏗️ Arquitectura del Sistema

El proyecto implementa una arquitectura desacoplada y segura:

1.  **Backend (API):** Basado en **FastAPI** y **PostgreSQL**.
    *   **Seguridad Dual:** Autenticación por **API_KEY** (para servicios y scripts) y **JWT (JSON Web Tokens)** para sesiones de navegador.
    *   **Aislamiento:** Middleware que garantiza que cada petición acceda exclusivamente a los datos de su propio `Tenant ID`.
2.  **Frontend (App):** Aplicación **Flet** multiplataforma (Web/APK).
    *   Optimización para producción mediante `flet build web` (CanvasKit).
    *   Gestión de sesiones administrativas seguras mediante tokens persistentes en memoria del cliente.
3.  **Redireccionamiento (Shortlinks):** Sistema de redirección rápida a nivel de servidor (HTTP 302) para enlaces de descarga (ej: `/apk`) y promociones.

---

## ✨ Características Principales

*   **Multi-tenancy Real:** Aislamiento de datos por `Tenant ID` en una base de datos centralizada.
*   **Gestión Dinámica:** Catálogo, grupos de opciones, precios y descuentos editables en tiempo real.
*   **Seguridad Industrial:** Claves ocultas mediante variables de entorno y tokens de sesión firmados (HS256).
*   **Acortador Inteligente:** Redirección instantánea gestionada desde el panel administrativo (Backend-level).
*   **Panel Administrativo Pro:** Control total de pedidos, estados de entrega, configuración de marca y exportación de datos (CSV/Excel/PDF).

---

## 🚀 Instalación y Configuración

### Requisitos
*   Python 3.10+
*   PostgreSQL (Producción) / SQLite (Pruebas locales)

### 1. Preparar el Entorno
```bash
git clone https://github.com/ivam3/proyectos_flet.git
cd delivery_apps
```

### 2. Configuración de Seguridad (OBLIGATORIO)
El sistema depende de una clave maestra llamada `API_SECRET_KEY`. Debes configurarla en todos los servicios:

*   **Localmente:** Crea archivos `config.py` en las carpetas `src/` basándote en los `.example` y asigna tu clave.
*   **Producción:** Configura la variable de entorno `API_SECRET_KEY` en Railway para el Backend y todos los Frontends.

---

## 🛠️ Gestión con db_admin.py

Esta herramienta CLI permite el control técnico total sin entrar a la web.

```bash
# Iniciar administración de un negocio
python db_admin.py [nombre_directorio_negocio]
```

### Comandos Principales:
*   `importar [archivo.json]`: Sincronización inteligente de datos (Upsert por ID/Nombre).
*   `addlink [codigo] [url]`: Configura una redirección corta (ej: `addlink apk http://...`).
*   `backup [archivo.json]`: Respaldo completo del tenant actual.
*   `upload [imagen]`: Sube imágenes al servidor con conversión automática a WebP.

---

## 🌐 Despliegue en Railway

1.  **Backend:** Conectar el repo, configurar `DATABASE_URL` y `API_SECRET_KEY`.
2.  **Frontends:** Configurar `API_URL`, `TENANT_ID` y la misma `API_SECRET_KEY`.
3.  **URLs de Redirección:** Disponibles en `https://tu-api.up.railway.app/r/{tenant}/{codigo}`.

---

## 📱 Compilación APK
Para generar el instalador Android:
```bash
flet build apk --verbose
```

---

## 📝 Créditos
Desarrollado por **Ivam3byCinderella**. © 2026 Todos los derechos reservados.
