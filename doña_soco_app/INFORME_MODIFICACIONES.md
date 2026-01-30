# Informe Final de Modificaciones y Diagnóstico

## Resumen Ejecutivo
Después de un extenso proceso de depuración, se logró identificar y solucionar una serie de problemas complejos que impedían el correcto funcionamiento de la aplicación, especialmente la subida de imágenes y el arranque en modo web. La solución final se basa en utilizar la versión estable de Flet (`0.28.3`) y la implementación correcta de solicitud de permisos en Android.

---

### 1. Aislamiento del Carrito de Compras (Realizado Previamente)
*   **Estado:** Completado.
*   **Detalle:** Se refactorizó el sistema para que cada usuario tenga un carrito de compras independiente usando `page.session`, solucionando el problema de carritos compartidos entre clientes.

### 2. Solución Definitiva a la Carga de Imágenes y Arranque de la App
*   **Problema Principal:** La aplicación presentaba dos problemas críticos:
    1.  No arrancaba en modo web, quedándose en una pantalla de carga infinita.
    2.  La subida de imágenes fallaba en Android con un error de "ruta no accesible".

*   **Proceso de Diagnóstico y Solución:**
    1.  **Cuelgue de la Aplicación:** Se identificó que la causa del cuelgue era una lógica de subida de archivos implementada en `menu_admin.py` que usaba `httpx` para re-descargar un archivo recién subido, creando un bloqueo en el servidor de Flet.
    2.  **Versiones de Flet:** Se investigó una posible inconsistencia en las versiones de Flet. Se determinó, con la ayuda del usuario, que la versión **estable `0.28.3`** era la funcional, mientras que las versiones de pre-lanzamiento presentaban bugs insuperables (`KeyError: 'bytes'`).
    3.  **Permisos en Android:** Se confirmó que el error "ruta no accesible" en la versión estable se debía a la falta de permisos de almacenamiento en Android.
    4.  **Implementación Final:** Se ha modificado el archivo `app/src/panel_restaurante/views/menu_admin.py` para reflejar la solución definitiva y estable:
        *   Se eliminó por completo la lógica `httpx` que causaba el cuelgue.
        *   Se reintrodujo el `PermissionHandler` para solicitar permisos de almacenamiento de forma explícita en Android antes de abrir el selector de archivos (`pick_files`).
        *   Se utiliza el método simple y directo `shutil.copy` para guardar la imagen una vez que se obtiene la ruta válida gracias al permiso concedido.

### 3. Estandarización y Actualizaciones de API
*   **Rutas de Imágenes:** Se han estandarizado todas las rutas de las imágenes (`Image.src`) en los archivos (`main.py`, `menu_admin.py`, `views/menu.py`) al formato correcto (`/{nombre_archivo}`) para que se muestren adecuadamente.
*   **Llamada a Flet:** Se ha verificado que `main.py` utiliza `ft.app()`, que es la función correcta para la versión estable `0.28.3` de Flet.

### 4. Corrección de Exportación en Gestión de Pedidos
*   **Problema:** Los botones de exportación (CSV, XLSM, PDF) en `pedidos.py` no generaban ningún archivo, aunque mostraban mensajes de éxito. Esto se debía a que `FilePicker.save_file` no escribe automáticamente el contenido en el disco en el entorno nativo/Termux, solo obtiene la ruta de destino.
*   **Solución:**
    *   Se implementó un mecanismo de estado (`pending_save_content`) para retener los bytes del archivo generado (CSV o PDF) temporalmente.
    *   Se actualizó el manejador `on_file_picker_result` en `app/src/panel_restaurante/views/pedidos.py` para detectar cuando se selecciona una ruta de guardado y escribir explícitamente el contenido almacenado en ese archivo usando operaciones de E/S estándar de Python (`open(..., "wb")`).

### 5. Corrección de Conflicto en Selector de Archivos (Gestión de Pedidos)
*   **Problema:** La sección "Gestión de Pedidos" dejó de cargar tras la implementación de la exportación. Esto se debió a un conflicto al reutilizar el objeto `FilePicker` global que también era usado por el panel de menú. Al sobrescribir sus eventos (`on_result`), se generaban inconsistencias o bloqueos silenciosos al inicializar la vista.
*   **Solución:**
    *   Se aisló la funcionalidad de gestión de archivos en `pedidos.py` creando una instancia local de `ft.FilePicker` exclusiva para esta vista.
    *   Este `FilePicker` local se agrega a `page.overlay` internamente y maneja sus propios eventos de guardado, evitando interferencias con el resto de la aplicación.

### 6. Corrección de Bug Visual "Red Stripe" (Android)
*   **Problema:** Al agregar el `FilePicker` local a `page.overlay` en la corrección anterior, reapareció el error visual conocido en Android (franja roja con "Unknown method: FilePicker"). Esto confirma que en este entorno/versión, los controles no visuales no deben ir al overlay directo.
*   **Solución:**
    *   Se eliminó `page.overlay.append(file_picker)` en `pedidos.py`.
    *   Se integró el `FilePicker` directamente en el árbol de controles de la vista, envuelto en un `ft.Container(visible=False)`. Esto mantiene la funcionalidad aislada (evitando conflictos con el global) y respeta las limitaciones de renderizado de la plataforma.

### 7. Corrección Visual en Menú de Usuario (PC/Web)
*   **Problema:** En navegadores de escritorio (Chrome PC), los elementos de las tarjetas del menú (precio y botón de agregar) se superponían a la descripción del platillo debido a una altura insuficiente de la tarjeta.
*   **Diagnóstico:** La propiedad `child_aspect_ratio` del `GridView` estaba configurada en `1.1` para pantallas grandes, lo que generaba tarjetas demasiado cortas cuando el ancho de la columna se reducía dinámicamente.
*   **Solución:** Se ajustó el `child_aspect_ratio` a `0.8` en `app/src/views/menu.py` para la vista de escritorio. Esto aumenta la altura relativa de las tarjetas, asegurando espacio suficiente para la imagen, título, descripción (hasta 3 líneas) y los controles inferiores sin superposiciones.

### 8. Activación de Carga de Archivos (FLET_SECRET_KEY)
*   **Problema:** Error `ERROR GENERAL: Specify secret_key parameter...` al intentar subir imágenes en el panel de administración.
*   **Diagnóstico:** Flet requiere una clave secreta (`secret_key`) para firmar las URLs de carga de archivos. La función `ft.run()` utilizada en esta versión no admite el parámetro `secret_key` directamente.
*   **Solución:** Se estableció la variable de entorno `os.environ["FLET_SECRET_KEY"] = "ads2025_dona_soco_secret"` en `app/src/main.py` antes de llamar a `ft.run()`. Esto habilita la funcionalidad de subida de archivos necesaria para la gestión del menú.

### 9. Corrección en Subida de Archivos (FilePickerUploadFile)
*   **Problema:** Error `TypeError: FilePickerUploadFile.__init__() got multiple values for argument 'upload_url'` al seleccionar una imagen.
*   **Diagnóstico:** La firma del constructor `FilePickerUploadFile` en la versión instalada de Flet es `(upload_url, method, id, name)`.
*   **Solución:** Se usaron argumentos de palabra clave explícitos: `ft.FilePickerUploadFile(name=archivo.name, upload_url=upload_url)`.

### 10. Manejo Asíncrono de Subida (AWAIT)
*   **Problema:** `RuntimeWarning: Enable tracemalloc...` y la subida no se completaba.
*   **Diagnóstico:** En la versión actual de Flet, el método `file_picker.upload()` es una corrutina (async) y debe ser esperada con `await`.
*   **Solución:** Se convirtió la función `on_file_picked` a `async def` y se añadió `await` tanto a la llamada de `file_picker.upload()` como a la invocación de `on_file_picked(files)` dentro del controlador de eventos.

### 11. Corrección Método HTTP de Subida (405 Method Not Allowed)
*   **Problema:** Error `Upload endpoint returned code 405` al intentar subir la imagen.
*   **Diagnóstico:** El método predeterminado de subida en `FilePickerUploadFile` es `PUT`, pero el endpoint de carga del servidor Flet (en esta configuración/versión) parece requerir `POST`.
*   **Solución:** Se especificó explícitamente `method="POST"` en la instanciación de `ft.FilePickerUploadFile` dentro de `menu_admin.py`.

### 12. Solución Híbrida de Exportación de Archivos (Web/Desktop vs Android)
*   **Problema Complejo:** 
    1.  En **Android (APK)**, el uso del componente nativo `FilePicker` provocaba congelamientos (hangs) de la aplicación al intentar guardar archivos binarios (`save_file` con `src_bytes`).
    2.  En **Web/Escritorio**, el método de "Escritura Directa" (`open(path, 'wb')`) guarda el archivo en el sistema de archivos del servidor/host, no en el dispositivo del cliente.
*   **Solución Definitiva:** Se implementó una lógica condicional basada en la plataforma:
    *   **Para Web y Escritorio (Windows/Mac/Linux):** Se utiliza el `FilePicker` estándar. Esto permite al usuario elegir la ruta y gestiona la descarga vía navegador o diálogo del SO.
    *   **Para Android/iOS:** Se utiliza una función de "Escritura Directa Inteligente". Intenta guardar primero en `/storage/emulated/0/Download` (carpeta pública) y, si falla por permisos, en el directorio interno de la app.
    *   **Mejora UX Android:** Se reemplazó la notificación simple por un **Popup (AlertDialog)** que confirma explícitamente el éxito y muestra la ruta completa donde se guardó el archivo, facilitando su localización al usuario.
    *   **Layout:** Tras validar que los botones responden correctamente, se restauró el scroll general de la vista para maximizar el espacio de la tabla de pedidos.

### 13. Diagnóstico de Arquitectura y Sincronización (Actual)
*   **Problema Detectado:** Aislamiento de datos entre clientes. Actualmente, la aplicación utiliza una base de datos SQLite local (`dona_soco.db`) en cada dispositivo (APK Android, Navegador Web).
*   **Consecuencia:** Los pedidos realizados en un dispositivo no son visibles para el administrador ni para otros usuarios, ya que no existe una fuente de verdad centralizada.
*   **Solución Propuesta:** Migración a arquitectura Cliente-Servidor.
    *   **Backend:** Implementar una API REST con **FastAPI**.
    *   **Base de Datos:** Migrar de SQLite local a una base de datos centralizada (PostgreSQL/MySQL) alojada en la nube.
    *   **Frontend (App):** Refactorizar la capa de datos (`database.py`) para consumir la API mediante `httpx` en lugar de ejecutar consultas SQL directas.

### 14. Corrección de "Unknown control: FilePicker" en Seguimiento (PC Web)
*   **Problema:** Al acceder a la vista de "Seguimiento" desde un navegador en PC (modo Web), aparecía una franja roja con el error "Unknown control: FilePicker". Sin embargo, en navegadores Android funcionaba correctamente.
*   **Diagnóstico:**
    *   El código detectaba correctamente el entorno (PC vs Android). En Android, el `FilePicker` se omitía intencionalmente (usando escritura directa), por eso no fallaba.
    *   En PC, el código intentaba agregar el `FilePicker` directamente a `page.overlay`. En ciertas configuraciones de Flet Web/CanvasKit, agregar controles no visuales directamente al overlay provoca errores de renderizado si no están envueltos o gestionados correctamente.
*   **Solución:**
    *   Se modificó `app/src/views/seguimiento.py` para **no** agregar el `FilePicker` al `page.overlay`.
    *   En su lugar, se envolvió el `FilePicker` dentro de un `ft.Container(visible=False)` y se añadió este contenedor a la lista de controles (`ft.Column`) de la propia vista. Esto asegura que el control esté presente en el árbol de widgets sin interferir visualmente y sin causar conflictos de renderizado.

