# Informe de Modificaciones - Tortas Las Originales / Dona Soco Multi-tenant

## 2026-02-23 - Implementación de Multi-tenencia (Tenant Isolation)

### Objetivo
Adaptar el backend y el frontend para soportar múltiples clientes (tenants) utilizando una única base de datos y una única instancia de API, permitiendo que cada negocio tenga su propio inventario, configuración y pedidos.

### Cambios en el Backend
- **Modelos (`backend/models.py`):**
    - Se añadió la columna `tenant_id` (indexada) a todas las tablas: `Menu`, `GrupoOpciones`, `Configuracion`, `Orden`, `OrdenDetalle`, y `HistorialEstado`.
    - `tenant_id` tiene un valor por defecto de `'dona_soco'` para retrocompatibilidad con los datos existentes.
- **Esquemas (`backend/schemas.py`):**
    - Se incluyó `tenant_id` como campo opcional en los esquemas Base y Create.
- **CRUD (`backend/crud.py`):**
    - Se actualizaron todas las funciones de consulta para filtrar por `tenant_id`.
    - Se actualizaron las funciones de creación para persistir el `tenant_id` correspondiente.
    - `get_configuracion` ahora es capaz de crear una configuración inicial por cada tenant si no existe.
- **API Main (`backend/main.py`):**
    - Se implementó una dependencia `get_tenant_id` que extrae el identificador del encabezado `X-Tenant-ID`.
    - Se actualizaron todos los endpoints para requerir y utilizar esta dependencia.
    - Se mejoró la función `ensure_columns` para realizar la migración automática de la columna `tenant_id` en tablas existentes.
    - Se cambió el título de la API a "Delivery Multi-tenant API".

### Cambios en el Frontend
- **Configuración (`app/src/config.py`):**
    - Se añadió la variable `TENANT_ID`, cargada desde variables de entorno (por defecto `'tortas_las_originales'`).
    - Se incluyó `X-Tenant-ID` en los `HEADERS` globales de todas las peticiones HTTP.

### Resultado
El sistema ahora permite el despliegue de múltiples frontends (ej. Doña Soco y Tortas Las Originales) apuntando a la misma API. Cada frontend se identifica mediante su `TENANT_ID`, y el backend garantiza que los datos servidos y guardados pertenezcan exclusivamente a ese cliente.

### 2026-02-23 - Centralización de Backend y Automatización de CI/CD
*   **Backend Único:** Se eliminó la duplicidad de backends. Ahora ambos negocios usan el código en `delivery_apps/backend/`.
*   **Aislamiento de Datos:** Se verificó y aseguró la persistencia del `tenant_id` en todas las operaciones de base de datos (Menu, Pedidos, Config).
*   **GitHub Actions:** Se integró este proyecto al flujo de construcción automática de la web (`.github/workflows/flet-web.yml`).
