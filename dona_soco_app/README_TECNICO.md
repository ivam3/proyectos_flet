# Documentación Técnica: Proyecto Doña Soco App

## 1. Visión General del Proyecto
Esta aplicación es un sistema de gestión de pedidos para un restaurante ("Antojitos Doña Soco"). 
Está construida con **Python** utilizando una arquitectura híbrida:
- **Frontend:** Flet (Framework UI basado en Flutter). Funciona como App Móvil (Android/APK), Web App y Aplicación de Escritorio.
- **Backend:** FastAPI (API REST). Gestiona la lógica de negocio y la base de datos centralizada.

---

## 2. Arquitectura y Flujo de Datos
... [Sección sin cambios significativos] ...

---

## 3. Estructura de Directorios y Archivos Clave

### 📂 `app/src/`
*   `main.py`: **Punto de entrada.** Configura el entorno, manipula `sys.path` para Android, y define las rutas principales.
*   `database.py`: Capa de servicio que consume la API REST usando `httpx`.

#### 📂 `app/src/app_views/` (Vistas del Cliente)
*   `menu.py`: Grid responsive de platillos con búsqueda.
*   `carrito.py`: Gestión local del carrito de compras.
*   `checkout.py`: Validación de direcciones y registro de pedidos.
*   `seguimiento.py`: Rastreo en tiempo real y descarga de PDF.

#### 📂 `app/src/panel_restaurante/` (Vistas del Administrador)
*   `admin_panel.py`: Layout con navegación lateral/superior.
*   `admin_views/menu_admin.py`: Gestión de platillos y áreas de impresión.
*   `admin_views/pedidos.py`: Gestión de comandas e **Impresión Automática**.
*   `admin_views/configuracion.py`: Ajustes globales, guisos y salsas.

#### 📂 `app/src/components/`
*   `notifier.py`: Centraliza las notificaciones (`show_notification`) y el sonido.

---

## 4. Sistema de Impresión Inteligente y Automática

El sistema optimiza el flujo de cocina sin intervención manual:
1.  **Asignación:** Cada platillo tiene un `printer_target` ("cocina" o "foodtruck").
2.  **Automatización:** Al recibir un pedido, el PubSub activa `imprimir_pedido` automáticamente.
3.  **Desglose:** 
    *   **Caja:** Recibe ticket completo.
    *   **Cocina:** Solo items asignados a cocina.
    *   **Foodtruck:** Solo items asignados a foodtruck.

---

## 5. Dependencias Críticas (`pyproject.toml` / `requirements.txt`)

*   `flet` & `flet_core` (0.80.5): UI Framework.
*   `httpx`: Cliente para comunicación con FastAPI.
*   `fpdf2`: Generación de comprobantes.
*   `openpyxl`: Exportación a Excel.

---

## 6. Notas de Embalaje (APK Android)

Para resolver errores de módulo en Android:
- **Nombre de Carpetas:** Se usan prefijos como `app_views` para evitar conflictos con namespaces de Python/Android.
- **Packages:** Cada carpeta contiene un `__init__.py`.
- **Bootstrapping:** `main.py` debe insertar `os.path.dirname(__file__)` al inicio de `sys.path`.
- **Comando de Build:** `flet build apk` (desde la carpeta `@app/`).

---

## 7. Cómo Ejecutar el Proyecto
... [Sección sin cambios] ...
