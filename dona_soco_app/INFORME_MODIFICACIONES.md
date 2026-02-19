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

### 25. Mejora de Seguridad en Backend (Secrets)
*   **Cambio:** Se eliminaron las contraseñas en texto plano de `backend/crud.py`.
*   **Solución:** Ahora el sistema utiliza `os.getenv("API_SECRET_KEY")` para la llave maestra y `os.getenv("DEFAULT_ADMIN_PASSWORD")` para la contraseña inicial, mejorando la seguridad en entornos de producción como Railway.

### 26. Enriquecimiento de Comprobantes PDF
*   **Cambio:** Se mejoró la generación de PDF en `seguimiento.py` y `pedidos.py`.
*   **Solución:** Se añadió el logo del negocio en el encabezado y un pie de página con el nombre, teléfono y dirección del negocio (obtenidos dinámicamente de la configuración).

### 27. Corrección de Selector de Imágenes en Menú Admin
*   **Problema:** El botón de subir imagen no abría el selector de archivos debido a que el `FilePicker` no estaba en el overlay o el handler fallaba.
*   **Solución:** Se aseguró que el `FilePicker` esté en `page.overlay` y se corrigió el handler `on_pick_files` manteniendo su naturaleza asíncrona (`async def` con `await`) para ser compatible con Flet 0.24+, resolviendo un SyntaxError accidental.

### 28. Estandarización de Notificaciones en Configuración
*   **Cambio:** Se reemplazaron los SnackBars por un `AlertDialog` de éxito al guardar la configuración.
*   **Solución:** Se homologó el feedback visual con el de la sección de pedidos para garantizar que el usuario reciba la confirmación de guardado de forma clara.

### 29. Botones de Redes Sociales y Flexibilidad
*   **Cambio:** Se agregaron iconos de Facebook, WhatsApp, Instagram y X en el encabezado global.
*   **Solución:** Las URLs son ahora editables desde el panel de Configuración. Si un campo queda vacío, el botón correspondiente no se muestra en el encabezado.

### 30. Solución de Carga en Firefox (WebGL/CanvasKit)
*   **Problema:** La aplicación no cargaba en Firefox debido a advertencias/errores de WebGL con CanvasKit.
*   **Solución:** Se cambió el renderizador web a `web_renderer="auto"` en `main.py`, permitiendo que Firefox utilice el motor HTML cuando sea necesario, evitando el bloqueo por deprecación de extensiones WebGL.

### 31. Corrección de Deprecación de Padding en main.py
*   **Problema:** Advertencia `DeprecationWarning: only() is deprecated since version 0.80.0. Use Padding.only() instead`.
*   **Solución:** Se actualizó el uso de `ft.padding.only` por `ft.Padding.only` en `main.py` para cumplir con los estándares de las versiones más recientes de Flet.

### 32. Corrección de Corrutinas en Lanzamiento de URLs
*   **Problema:** `RuntimeWarning` por no esperar (await) la corrutina de `page.launch_url` en los botones de redes sociales y `AttributeError` al intentar usar métodos inexistentes en `page.session`. Además, `ft.UrlLauncher` causaba un error de "Unknown control" en el cliente web de esta versión.
*   **Solución:** Se revirtió el uso de `ft.UrlLauncher` y se volvió a `page.launch_url`, pero asegurando que todas las llamadas sean asíncronas (`await page.launch_url(...)`). Esto elimina el `RuntimeWarning` y garantiza el funcionamiento de los enlaces, aceptando el `DeprecationWarning` como inevitable en la versión actual de Flet para mantener la estabilidad del cliente web.

### 33. Fix de Iconos y Robustez en Descargas Web
*   **Problema:** La aplicación no iniciaba (`AttributeError: X`) porque el icono `ft.Icons.X` no existe en Flet 0.80.5. Además, archivos grandes (>1MB) en Base64 causaban desconexiones del WebSocket.
*   **Solución:** 
    1. Se sustituyó `ft.Icons.X` por `ft.Icons.SHARE` en el encabezado global.
    2. Se añadió monitoreo de tamaño y logs de depuración en las funciones de descarga web en `seguimiento.py` y `pedidos.py` para identificar colapsos por archivos excesivamente grandes.

### 34. Rediseño Estético del Header y Estabilización de FilePicker
*   **Problema:** Los iconos de redes sociales eran demasiado grandes y desplazaban el nombre del negocio, afectando la estética. El selector de imágenes en el panel de administración dejó de abrirse al ser asíncrono en Flet 0.80.5.
*   **Solución:** 
    1. Se rediseñó el `top_bar` en `main.py` usando iconos más pequeños (`icon_size=18`), un `Row` ajustado (`tight=True`) y centrando el nombre del negocio con un `Container(expand=True)`.
    2. Se cambió el disparador `on_pick_files` en `menu_admin.py` a modo síncrono, lo que garantiza la apertura del diálogo del sistema en versiones antiguas de Flet.

### 35. Fix de Atributos de Alineación y Ciclo de Vida de Vistas
*   **Problema:** `AttributeError: module 'flet.controls.alignment' has no attribute 'center'` al intentar alinear el texto del header. Además, el `FilePicker` volvía a fallar al cambiar de pestaña dentro del Panel de Administración debido al cache de vistas.
*   **Solución:** 
    1. Se sustituyó `ft.alignment.center` por `ft.alignment.Alignment(0, 0)` en `main.py`, compatible con la estructura de módulos de Flet 0.80.5.
    2. Se eliminó el `views_cache` en `admin_panel.py`, forzando la reinicialización de las vistas al cambiar de pestaña. Esto asegura que el `FilePicker` y sus handlers se registren correctamente en el `overlay` de la página cada vez que se accede a la Gestión de Menú.

### 36. Rediseño Profesional de Header y Solución de Corrutinas
*   **Problema:** El header era demasiado alto y los iconos de redes sociales causaban el truncado del nombre del negocio ("Antojit..."). Además, el selector de imágenes lanzaba un `RuntimeWarning` al no esperar la corrutina `pick_files`.
*   **Solución:** 
    1. Se rediseñó el header en `main.py` integrando las redes sociales en un `ft.PopupMenuButton` (icono ⋮), liberando espacio horizontal. 
    2. Se redujo el padding vertical del header y el tamaño del logo para una apariencia más compacta y profesional.
    3. Se restauró `on_pick_files` como asíncrono (`async def` con `await`) en `menu_admin.py`, eliminando el `RuntimeWarning` y restaurando la funcionalidad del selector de archivos bajo el nuevo ciclo de vida de vistas sin caché.

### 37. Corrección de Compatibilidad en PopupMenuItem y Padding
*   **Problema:** `TypeError: PopupMenuItem.__init__() got an unexpected keyword argument 'text'` y `DeprecationWarning` por el uso de `ft.padding.symmetric`.
*   **Solución:** 
    1. Se cambió el argumento `text` por `content=ft.Text(...)` en los elementos del `PopupMenuButton` para ser compatible con la firma de `ft.PopupMenuItem` en Flet 0.80.5.
    2. Se actualizó el uso de `ft.padding.symmetric` a `ft.Padding.symmetric` en `main.py` para eliminar advertencias de deprecación.

### 38. Homologación Visual de Header y Footer
*   **Cambio:** Se ajustaron las dimensiones del header (`top_bar`) para que tenga una presencia visual simétrica con el footer (`NavigationBar`).
*   **Solución:** Se aumentó el padding vertical a `5` y el tamaño del logo a `35px`, además de subir el tamaño de la fuente del título a `18`. Esto crea un equilibrio estético entre la parte superior e inferior de la aplicación, mejorando la jerarquía visual.