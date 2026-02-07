# Manual de Usuario
# Sistema de Gestión

**Versión del Documento:** 1.0  
**Fecha de Actualización:** 30 de Enero de 2026

---

## Índice

1. [Introducción](#1-introducción)
2. [Acceso al Sistema](#2-acceso-al-sistema)
3. [Módulo de Clientes (App de Pedidos)](#3-módulo-de-clientes-app-de-pedidos)
    - Exploración del Menú
    - Personalización de Platillos
    - Carrito y Checkout
    - Seguimiento de Pedidos
4. [Panel de Administración](#4-panel-de-administración)
    - Gestión del Menú (Platillos)
    - Configuración de Áreas de Impresión
    - Gestión de Pedidos
    - Sistema de Impresión Inteligente
    - Reportes y Exportación
5. [Solución de Problemas Frecuentes](#5-solución-de-problemas-frecuentes)

---

## 1. Introducción

Bienvenido al manual de uso de la aplicación. Este sistema permite a los clientes realizar pedidos de forma digital y al personal administrativo gestionar la cocina, las ventas y la logística del restaurante de manera eficiente.

El sistema es híbrido y cuenta con soporte para impresión distribuida en distintas áreas (Caja, Cocina Interior y Foodtruck Exterior).

---

## 2. Acceso al Sistema

### Para Clientes
Los clientes acceden a la aplicación directamente desde la pantalla de inicio. No se requiere registro previo para ver el menú.

### Para Administradores
1.  En el menú lateral de la aplicación, seleccione el encabezado de la aplicación.
2.  Ingrese la contraseña de administración proporcionada por el encargado.
3.  Al ingresar correctamente, será redirigido al **Panel de Administración**.

---

## 3. Módulo de Clientes (App de Pedidos)

### Exploración del Menú
*   El menú muestra todos los platillos disponibles con sus precios e imágenes.
*   **Búsqueda:** Utilice la barra superior para encontrar platillos por nombre.
*   **Descripciones:** Ahora puede leer la descripción completa de los ingredientes pulsando sobre el texto del platillo.

### Personalización de Platillos
Al seleccionar un producto (ej. "Gordita" o "Burrito"), si el platillo lo permite, podrá seleccionar:
*   **Guisos:** Opciones principales del platillo.
*   **Salsas:** Acompañantes o nivel de picante.
*   **Cantidad:** Número de piezas a ordenar.
*   **Notas Especiales:** Campo de texto libre para instrucciones adicionales (ej. "Sin lechuga").

### Carrito y Checkout
1.  Presione el icono del **Carrito** para ver su resumen.
2.  Puede aumentar o disminuir cantidades.
3.  Presione **"ir a checkout"**.
4.  Seleccione el método de entrega:
    *   **Envío a Domicilio:** Requiere dirección y teléfono.
    *   **Recoger en Tienda:** Elimina el costo de envío.
5.  Confirme el pedido. Recibirá un **Código de Seguimiento** (ej. `XR5T9`). **¡Guárdelo!**

### Seguimiento de Pedidos
1.  Vaya a la sección **"Seguimiento"**.
2.  Ingrese su número de teléfono y el código de seguimiento.
3.  Podrá ver el estado en tiempo real:
    *   🔵 *Pendiente*
    *   🟠 *Preparando*
    *   🚚 *En Camino*
    *   🟢 *Entregado*
4.  **Descargar Ticket:** Puede descargar un comprobante en PDF de su compra desde esta pantalla.

---

## 4. Panel de Administración

Este panel es exclusivo para el personal del restaurante.

### Gestión del Menú (Platillos)
En la sección **"Gestion de Menú"**, puede:
*   **Agregar:** Llene el formulario con nombre, precio, descripción y foto.
*   **Editar:** Presione el lápiz ✏️ sobre un platillo existente.
*   **Ocultar:** Use el interruptor (Switch) para desactivar un platillo si se agota (sin borrarlo).
*   **Eliminar:** Presione el icono de basura 🗑️ (acción permanente).

### Configuración de Áreas de Impresión
Al crear o editar un platillo, encontrará una opción llamada **"Área de Preparación"**:

*   Seleccione **Cocina (Interior):** Para guisos, sopas, bebidas preparadas dentro.
    *   *Se identifica con una etiqueta AZUL en la lista.*
*   Seleccione **Foodtruck (Exterior):** Para antojitos de masa, frituras, etc.
    *   *Se identifica con una etiqueta NARANJA en la lista.*

> **Nota:** Esta configuración determina a qué impresora se enviará la comanda de este producto específico.

### Gestión de Pedidos
En la sección **"Pedidos"**, verá una tabla con todas las órdenes del día.
*   **Estados:** Use los botones para cambiar el estado del pedido (Pendiente -> Preparando -> En Camino).
*   **Cancelar:** Si cancela un pedido, el sistema le pedirá obligatoriamente un **motivo** (ej. "Cliente no contestó").

### Sistema de Impresión Inteligente
En la columna "Acciones" de la tabla de pedidos, encontrará un botón de **IMPRESORA (🖨️)**. Al presionarlo, el sistema automáticamente:

1.  Analiza qué productos contiene el pedido.
2.  **Impresora CAJA:** Imprime el ticket completo con totales para cobro.
3.  **Impresora COCINA:** Imprime *solo* los productos etiquetados como "Interior".
4.  **Impresora FOODTRUCK:** Imprime *solo* los productos etiquetados como "Exterior".

*Aparecerá un mensaje en pantalla confirmando a qué áreas se enviaron los tickets.*

### Reportes y Exportación
Puede descargar el historial de ventas usando los botones en la parte superior:
*   **CSV:** Formato compatible con cualquier hoja de cálculo.
*   **Excel:** Formato `.xlsx` con columnas separadas para análisis detallado.

---

## 5. Solución de Problemas Frecuentes

| Problema | Causa Probable | Solución |
| :--- | :--- | :--- |
| **No imprime en Foodtruck** | El platillo está configurado como "Cocina". | Vaya a Menú, edite el platillo y cambie el Área de Preparación a "Foodtruck". |
| **Error al subir imagen** | Archivo muy pesado o formato no válido. | Intente con imágenes JPG/PNG menores a 2MB. |
| **No aparece el pedido nuevo** | La lista no se ha actualizado. | Presione el botón "Refrescar" 🔄 o espere la notificación automática. |
| **App lenta en Android** | Muchos pedidos cargados en memoria. | Cierre y vuelva a abrir la aplicación. |

---
*Documento generado por Ivam3byCinderella.*
