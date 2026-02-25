# Informe Final de Modificaciones y Diagnóstico

## Resumen Ejecutivo
Después de un extenso proceso de depuración, se logró identificar y solucionar una serie de problemas complejos que impedían el correcto funcionamiento de la aplicación, especialmente la subida de imágenes y el arranque en modo web. La solución final se basa en utilizar la versión estable de Flet (`0.28.3` / `0.80.5` según entorno) y la implementación correcta de empaquetado para Android.

---

### 1 - 14. [Secciones Anteriores...]
*(Mantener el registro histórico de los puntos previos sobre Carrito, Permisos, Exportación y CSS)*

### 15. Centralización de Notificaciones (SnackBar)
*   **Problema:** Los avisos visuales (`ft.SnackBar`) no aparecían de forma consistente en Android al cambiar estados o realizar acciones.
*   **Solución:** Se creó una función centralizada `show_notification` en `app/src/components/notifier.py`. Esta función fuerza la apertura (`open=True`), limpia estados previos y establece una duración estándar, garantizando que el usuario siempre reciba feedback visual en PC y móvil.

### 16. Impresión Automática de Pedidos
*   **Problema:** El administrador debía presionar un botón manualmente para imprimir comandas.
*   **Solución:** Se actualizó el sistema PubSub en `app/src/panel_restaurante/admin_views/pedidos.py`. Ahora, al detectar un mensaje de `"nuevo_pedido"`, el sistema consulta automáticamente la última orden y dispara el flujo de impresión masiva (Caja, Cocina, Foodtruck) sin intervención humana.

### 17. Reestructuración de Módulos para APK (Fix ModuleNotFoundError)
*   **Problema:** Al compilar el APK, Android no encontraba la carpeta `views/`, lanzando errores de módulo.
*   **Diagnóstico:** El empaquetador de Flet en Android a veces tiene conflictos con nombres de carpeta genéricos como `views` o requiere una estructura de paquetes estricta.
*   **Solución:**
    1.  Se renombró la carpeta `src/views` a `src/app_views`.
    2.  Se renombró la carpeta `src/panel_restaurante/views` a `src/panel_restaurante/admin_views`.
    3.  Se crearon archivos `__init__.py` en todos los directorios de código para forzar el reconocimiento de paquetes en Python.

### 18. Corrección del Punto de Entrada y sys.path
*   **Problema:** La aplicación fallaba al iniciar por rutas de búsqueda incorrectas en el entorno móvil.
*   **Solución:** 
    1.  Se migró de `ft.run()` a `ft.app(target=main)` en `main.py`.
    2.  Se implementó una manipulación agresiva de `sys.path` al inicio de `main.py` para incluir el directorio raíz y su padre en la búsqueda de módulos.
    3.  Se añadió el bloque `if __name__ == "__main__":` para asegurar un arranque limpio del empaquetador.

### 19. Sincronización de Dependencias en pyproject.toml
*   **Problema:** Faltaban librerías de red en el APK, lo que impedía la comunicación con la API.
*   **Solución:** Se actualizaron las dependencias en `app/pyproject.toml` incluyendo explícitamente `httpx` y `httpcore`. Además, se sincronizó la versión de `flet_core` a la `0.80.5` para evitar discrepancias con el framework principal durante el build.

### 20. Estabilización de Exportación (Web/Escritorio) y Fix "Control must be added"
*   **Problema:** Al intentar exportar CSV/Excel o PDF en navegador, a veces no ocurría nada o se lanzaba el error `Control must be added to the page first`.
*   **Diagnóstico:** El control `FilePicker` se perdía del `overlay` durante la navegación entre rutas o al limpiar el estado en `logout`.
*   **Solución:** 
    1.  Se implementó una verificación dinámica de la propiedad `.page` de los pickers antes de cada uso.
    2.  Si el picker no está adjunto a la página, se re-inserta en el `overlay` de forma transparente.
    3.  Se eliminó `page.overlay.clear()` del flujo de `logout` para preservar los componentes globales.

### 21. Eliminación de "Unknown control: FilePicker" (Franja Roja)
*   **Problema:** Al añadir el `FilePicker` directamente al `overlay`, Flet mostraba una franja roja de error visual en el lateral izquierdo.
*   **Solución:** Se envolvió el `FilePicker` en un `ft.Container(visible=False)`. Esto permite que el control esté funcional en el árbol de la página (para diálogos de sistema) sin que el framework intente renderizar un área visual para él, eliminando el glitch gráfico.
*   **Configuración Final:** Se restauró el uso de `ft.run()` con el motor `canvas_kit` para máxima compatibilidad con la versión `0.80.0`.

### 22. Soporte para SPA Routing (Fix 404 en Reload)
*   **Problema:** Al recargar la página en Railway (ej: `/menu`), se obtenía un error 404.
*   **Solución:** Se actualizó el backend (`backend/main.py`) con una ruta "catch-all" que captura cualquier petición no reconocida y sirve el `index.html` del frontend. Esto permite que el enrutador interno de Flet tome el control de la URL después de la carga inicial.

### 23. Corrección del Botón de Checkout (Continuar Pedido)
*   **Problema:** El botón de confirmación de pedido a veces no realizaba ninguna acción o se quedaba bloqueado.
*   **Solución:** 
    1.  Se envolvió toda la lógica de `confirmar_pedido` en un bloque `try-except` global.
    2.  Se añadió feedback visual inmediato (`btn.text = "Procesando..."`) para indicar actividad al usuario.
    3.  Se aseguró la liberación del botón (`disabled=False`) en caso de error para permitir reintentos, informando al usuario mediante SnackBar.

### 24. Optimización de FilePicker para Builds Estáticos (flet build web)
*   **Problema:** La exportación funcionaba en desarrollo (`flet run`) pero no en producción tras el build.
*   **Diagnóstico:** Algunos navegadores ignoran la inicialización de controles dentro de contenedores con `visible=False` durante la carga de WebAssembly (Pyodide).
*   **Solución:** Se cambió `visible=False` por un contenedor "quasi-visible" con `width=1, height=1` y `opacity=0`. Esto garantiza que el navegador inicialice el control del sistema sin que sea visible para el usuario ni cause la franja roja de error.

### 25. Estabilización de FilePicker Global y Gestión de Referencias
*   **Problema:** El selector de imágenes en el menú administrativo no se abría al pulsar el botón.
*   **Diagnóstico:** En `main.py`, se intentaba re-encapsular el `FilePicker` en contenedores durante el cambio de rutas, lo que provocaba la pérdida de la referencia del control en el árbol de Flet.
*   **Solución:** Se simplificó la lógica en `main.py` y `menu_admin.py`. Los pickers ahora se añaden una sola vez al `overlay` global de la página y se accede a ellos directamente, garantizando que el evento `pick_files` siempre sea capturado por el sistema operativo.

### 26. Solución para Firefox y Sincronización de Framework
*   **Problema:** La aplicación no cargaba en Firefox, mostrando advertencias de WebGL obsoletas.
*   **Diagnóstico:** Inconsistencia crítica entre `flet` (0.80.5) y `flet_core` (0.24.1) en `pyproject.toml`, sumado a un renderizador HTML inestable para esta versión.
*   **Solución:** 
    1. Sincronización de versiones: Se forzó `flet_core==0.80.5` en las dependencias.
    2. Cambio de Motor: Se migró de `web_renderer="html"` a `CANVAS_KIT` en `main.py`, lo cual es más robusto para aplicaciones con gestión de estados complejos y Wasm.
    3. Se verificó que `nginx.conf` incluya las cabeceras COOP/COEP necesarias para el aislamiento de procesos de CanvasKit.

### 27. Optimización de Flujo de Configuración (Evitar Redundancia)
*   **Problema:** El usuario era cuestionado dos veces sobre salsas/guisos si el producto tenía tanto grupos dinámicos como configuración legacy, incluso si elegía "Sin salsa" en la primera.
*   **Solución:** 
    1. Se implementaron rastreadores internos (`_salsa_pieces_needed`, `_guiso_pieces_needed`) al iniciar el checkout.
    2. En los diálogos de grupos dinámicos, se añadió lógica para detectar opciones negativas (ej: "Sin salsa", "No", "Ninguno").
    3. Al detectar una opción negativa, se descuenta automáticamente la cantidad de piezas correspondientes de la configuración legacy.
    4. Los diálogos legacy ahora se saltan automáticamente si el rastreador llega a cero, eliminando la redundancia y mejorando la fluidez de compra.

### 28. Mejora de UX en Menú (Selector de Cantidad Dinámico)
*   **Problema:** Al agregar un producto, la app redirigía automáticamente al carrito, interrumpiendo el flujo de compra si el usuario quería agregar más cosas.
*   **Solución:** 
    1. Se eliminó la redirección automática al carrito en `menu.py`.
    2. Se sustituyó el botón estático de "Agregar" por un **Selector Dinámico** en cada tarjeta del menú.
    3. Si el producto no está en el carrito, se muestra el botón de compra.
    4. Al presionar "Agregar", el botón se transforma en un control `- 1 +`, permitiendo ajustar la cantidad directamente desde el menú.
    5. Se añadió el método `get_item_quantity` en la clase `Cart` para sincronizar las cantidades entre vistas.
    6. Este enfoque es más profesional y permite una compra más rápida y fluida.

### 29. Implementación de Multi-tenencia (Backend Centralizado)
*   **Cambio:** Se migró a un backend único para todos los negocios del proyecto.
*   **Solución:**
    1. Se añadió el campo `tenant_id` a todas las tablas de la base de datos.
    2. El API ahora requiere el encabezado `X-Tenant-ID` para filtrar menús, configuraciones y pedidos.
    3. Se implementó una migración automática que asigna `dona_soco` por defecto a los datos existentes.

### 30. Actualización de CI/CD (GitHub Actions)
*   **Cambio:** Se actualizó `.github/workflows/flet-web.yml`.
*   **Solución:** Ahora el flujo de trabajo construye automáticamente tanto `dona_soco_app` como `tortas_las_originales` en cada push a la rama `dev`, manteniendo ambos sitios actualizados en Railway.