# Documentación Técnica: Proyecto Doña Soco App

## 1. Visión General del Proyecto
Esta aplicación es un sistema de gestión de pedidos para un restaurante ("Antojitos Doña Soco"). 
Está construida con **Python** utilizando una arquitectura híbrida:
- **Frontend:** Flet (Framework UI basado en Flutter). Funciona como App Móvil (Android/APK), Web App y Aplicación de Escritorio.
- **Backend:** FastAPI (API REST). Gestiona la lógica de negocio y la base de datos.
- **Base de Datos:** SQLite (Relacional).

El sistema permite a los clientes ver el menú, armar un carrito, realizar pedidos (con envío o recoger en tienda) y rastrearlos. Para el administrador, ofrece un panel para gestionar el menú, actualizar estados de pedidos, exportar reportes y **gestionar la impresión de comandas**.

---

## 2. Arquitectura y Flujo de Datos

### Flujo General
1.  **Cliente (App Flet):** El usuario interactúa con la UI.
2.  **Capa de Comunicación (`database.py`):** La UI llama a funciones en este archivo.
3.  **Transporte (HTTPX):** Estas funciones envían peticiones HTTP (GET, POST, PUT) a la API local o remota.
4.  **Servidor (FastAPI):** Recibe la petición, valida datos con Pydantic (`schemas.py`) y llama al controlador de base de datos (`crud.py`).
5.  **Persistencia (SQLAlchemy):** Interactúa con el archivo `dona_soco.db` y devuelve la respuesta.

> **Nota Importante:** Actualmente, algunas partes del panel administrativo (ej. `pedidos.py`) leen directamente la base de datos SQLite por rendimiento en local, mientras que la app del cliente consume 100% la API.

---

## 3. Estructura de Directorios y Archivos Clave

### Raíz del Proyecto
*   `migrate.py`: Script de utilidad para inicializar o migrar la base de datos.
*   `backend_dona_soco.db` / `app/storage/data/dona_soco.db`: Archivos físicos de la base de datos SQLite.

### 📂 `app/` (El Frontend - Flet)
El núcleo de la interfaz de usuario.

#### `app/src/`
*   `main.py`: **Punto de entrada.** Configura la ventana, rutas de navegación, inicializa la sesión del carrito y maneja el cambio de vistas.
*   `database.py`: **Puente Frontend-Backend.** Contiene funciones (`obtener_menu`, `guardar_pedido`) que usan `httpx` para hablar con la API.
*   `database_sqlite.py`: Versión legada/alternativa para conexión directa (uso limitado).

#### `app/src/views/` (Vistas del Cliente)
*   `menu.py`: Muestra las tarjetas de productos. Maneja la lógica de agregar al carrito.
    *   *Mejora UX:* Descripciones de platillos ampliadas para mejor legibilidad.
*   `carrito.py`: Visualiza los items seleccionados, permite editar cantidades y proceder al checkout.
*   `checkout.py`: Formulario de datos de entrega.
    *   *Lógica clave:* Checkbox "Recoger en restaurante" que oculta campos de dirección y anula costos de envío.
*   `seguimiento.py`: Permite al usuario buscar su pedido por teléfono/código.
    *   *Funcionalidad:* Muestra estado, historial, permite cancelar (si está pendiente) y **descargar comprobante PDF**.
    *   *Hack Android:* Usa detección de plataforma para evitar el uso de `FilePicker` en el overlay en Android, usando escritura directa en su lugar.
*   `login.py`: Acceso al panel administrativo.

#### `app/src/panel_restaurante/` (Vistas del Administrador)
*   `admin_panel.py`: Contenedor principal del layout administrativo (Sidebar + Área de contenido).
*   `views/menu_admin.py`: ABM (Alta, Baja, Modificación) de platillos.
    *   *Configuración:* Permite definir el **Área de Preparación** (`printer_target`) como "Cocina (Interior)" o "Foodtruck (Exterior)".
    *   *Visual:* Etiquetas de colores en la lista para identificar rápidamente el destino de impresión.
    *   *Imagenes:* Subida y gestión de fotos de platillos.
*   `views/pedidos.py`: Tabla de gestión de pedidos.
    *   *Funcionalidad:* Cambiar estados, cancelar pedidos, ver detalles.
    *   *Impresión Inteligente:* Botón para enviar tickets desglosados a múltiples impresoras (Caja, Cocina, Foodtruck) con confirmación en pantalla.
    *   *Exportación:* Generación de reportes CSV/Excel y comprobantes PDF.

#### `app/src/components/`
*   `cart.py`: Clase lógica del Carrito de Compras (gestión de sesión en memoria).
*   `notifier.py`: Sistema PubSub para notificaciones en tiempo real (ej. cuando cambia un estado).

### 📂 `backend/` (El Servidor - FastAPI)
*   `main.py`: Inicialización de la App FastAPI, definición de rutas (endpoints) y configuración de CORS.
*   `models.py`: Definición de tablas de la base de datos (SQLAlchemy).
    *   *Tablas:* `Menu` (incluye nuevo campo `printer_target`), `Orden`, `OrdenDetalle`, `Configuracion`, `HistorialEstado`.
*   `schemas.py`: Modelos Pydantic para validación y serialización de datos (Request/Response bodies).
*   `crud.py`: Lógica pura de base de datos (Creates, Reads, Updates, Deletes).

---

## 4. Sistema de Impresión Inteligente

El sistema cuenta con una lógica de enrutamiento de impresión para optimizar el flujo de trabajo en el restaurante:

1.  **Configuración:** Cada platillo tiene asignado un atributo `printer_target` ("cocina" o "foodtruck").
2.  **Disparador:** Botón de impresión en la vista de pedidos.
3.  **Enrutamiento:**
    *   **Impresora Caja:** Recibe siempre el ticket completo (Totales + Todos los items).
    *   **Impresora Cocina (Interior):** Recibe solo los items etiquetados como "Interior" (si existen en el pedido).
    *   **Impresora Foodtruck (Exterior):** Recibe solo los items etiquetados como "Exterior" (si existen en el pedido).
4.  **Confirmación:** El administrador recibe un feedback visual indicando a qué áreas se enviaron los tickets exitosamente.

---

## 5. Dependencias Críticas (`requirements.txt`)

*   **Core:**
    *   `flet`: Framework UI.
    *   `fastapi`: Framework API.
    *   `uvicorn`: Servidor ASGI para correr FastAPI.
*   **Datos:**
    *   `sqlalchemy`: ORM para base de datos.
    *   `pydantic`: Validación de datos.
*   **Utilidades:**
    *   `httpx`: Cliente HTTP asíncrono (usado por Flet para llamar a FastAPI).
    *   `fpdf`: Generación de PDFs (Comprobantes).
    *   `openpyxl`: Generación de archivos Excel (`.xlsx`).
    *   `python-multipart`: Necesario para subida de archivos (imágenes) en FastAPI.

---

## 6. Notas Específicas para Desarrollo en Android/Termux

### A. Subida de Archivos y FilePicker
En Android (Flet 0.28+), el control `FilePicker` no puede agregarse directamente al `page.overlay` si no se va a usar inmediatamente, ya que provoca un error visual (franja roja "Unknown Control").
*   **Solución:** En `seguimiento.py` y `pedidos.py`, detectamos la plataforma.
    *   **Escritorio/Web:** Usamos `FilePicker` normal.
    *   **Android:** Omitimos `FilePicker` y usamos funciones de escritura directa (`open(path, 'wb')`) en la carpeta `/storage/emulated/0/Download`.

### B. Rutas de Archivos
*   Termux tiene una estructura de archivos particular. Las rutas absolutas deben manejarse con cuidado usando `os.path.join(os.getcwd(), ...)` o rutas relativas desde la raíz del proyecto.

### C. Secret Key
Para que la subida de archivos funcione en Flet (uploads), se debe definir la variable de entorno `FLET_SECRET_KEY` antes de iniciar la app en `main.py`.

---

## 7. Cómo Ejecutar el Proyecto

### 1. Iniciar el Backend (Terminal 1)
```bash
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
```

### 2. Iniciar la App Flet (Terminal 2)
```bash
# Asegurarse de estar en la raíz del proyecto
python app/src/main.py
```

---

## 8. Guía de Colaboración Futura
*   **Agregar un campo a la BD:**
    1.  Modificar `backend/models.py`.
    2.  Modificar `backend/schemas.py`.
    3.  Si es SQLite local, borrar la DB y reiniciar (o usar Alembic si se configura a futuro).
    4.  Actualizar `app/src/database.py` para enviar el nuevo campo.
    5.  Actualizar las Vistas (`app/src/views/...`).

*   **Depuración:**
    *   Usa `print(f"DEBUG: ...")` generosamente. En Termux, la salida estándar es tu mejor herramienta de diagnóstico.
    *   Revisa `backend.log` (si se configura logging) o la salida de Uvicorn para errores de API.