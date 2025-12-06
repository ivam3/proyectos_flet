# Informe de Modificaciones y Guía de Buenas Prácticas en Flet

Este documento detalla los cambios realizados en el archivo `app/src/main.py` para solucionar las advertencias de funciones obsoletas (`DeprecationWarning`) y modernizar el código a las últimas convenciones de Flet (versión 0.23.0+).

## Resumen de Cambios

A continuación se explican las advertencias, la forma antigua de escribir el código y la nueva forma correcta de hacerlo.

---

### 1. Dimensiones de la Ventana

- **Advertencia:** `window_width is deprecated... Use Page.window.width instead.` y `window_height is deprecated... Use Page.window.height instead.`
- **Motivo:** Las propiedades para controlar la ventana ahora están agrupadas bajo el objeto `page.window`.

- **Código Antiguo:**
  ```python
  page.window_width = 400
  page.window_height = 700
  ```

- **Código Nuevo:**
  ```python
  page.window.width = 400
  page.window.height = 700
  ```

---

### 2. Manejo de Colores e Iconos

- **Advertencia:** `colors enum is deprecated... Use Colors enum instead.` y `icons enum is deprecated... Use Icons enum instead.`
- **Motivo:** Flet ha estandarizado el uso de enumeraciones (Enums) para los nombres de colores e iconos, usando `PascalCase` (ej. `ft.Colors` y `ft.Icons`).

- **Código Antiguo:**
  ```python
  # Para colores
  ft.Text("...", color=ft.colors.GREY)
  
  # Para iconos
  ft.ElevatedButton("...", icon=ft.icons.SAVE)
  ```

- **Código Nuevo:**
  ```python
  # Para colores
  ft.Text("...", color=ft.Colors.GREY) # "grey" también es válido

  # Para iconos
  ft.ElevatedButton("...", icon=ft.Icons.SAVE) # "save" también es válido
  ```

---

### 3. Destinos de la Barra de Navegación

- **Advertencia:** `NavigationDestination() is deprecated... Use NavigationBarDestination class instead.`
- **Motivo:** El nombre de la clase fue cambiado para ser más descriptivo y específico.

- **Código Antiguo:**
  ```python
  nav = ft.NavigationBar(
      destinations=[
          ft.NavigationDestination(icon=ft.Icons.RESTAURANT_MENU, label="Menú"),
      ]
  )
  ```

- **Código Nuevo:**
  ```python
  nav = ft.NavigationBar(
      destinations=[
          ft.NavigationBarDestination(icon=ft.Icons.RESTAURANT_MENU, label="Menú"),
      ]
  )
  ```

---

### 4. Uso de Capas Superpuestas (`overlay`) para Diálogos y Notificaciones

- **Advertencia:** `dialog is deprecated... Use Page.overlay.append(dialog) instead.` y `snack_bar is deprecated... Use Page.overlay.append(snack_bar) instead.`
- **Motivo:** Flet introdujo una capa especial llamada `overlay` para manejar todos los controles que deben mostrarse "por encima" del contenido principal, como diálogos, notificaciones (`SnackBar`), menús emergentes, etc. Esto centraliza y ordena la forma en que se muestran estos elementos.

#### Para Diálogos (`AlertDialog`)

- **Código Antiguo:**
  ```python
  dialog = ft.AlertDialog(...)
  page.dialog = dialog  # Se asigna directamente a page.dialog
  page.dialog.open = True
  page.update()
  ```

- **Código Nuevo:**
  ```python
  dialog = ft.AlertDialog(...)
  page.overlay.append(dialog) # Se añade a la lista overlay
  dialog.open = True
  page.update()
  ```

#### Para Notificaciones (`SnackBar`)

- **Código Antiguo:**
  ```python
  page.snack_bar = ft.SnackBar(ft.Text("..."))
  page.snack_bar.open = True
  page.update()
  ```

- **Código Nuevo:**
  Se recomienda crear una función auxiliar para simplificar la creación de notificaciones.

  ```python
  # Función auxiliar
  def show_snackbar(text):
      snack_bar = ft.SnackBar(ft.Text(text))
      page.overlay.append(snack_bar)
      snack_bar.open = True
      page.update()

  # Uso
  show_snackbar("Platillo agregado correctamente")
  ```

## Conclusión

Adoptar estas nuevas prácticas no solo eliminará las advertencias, sino que también hará tu código más robusto, legible y compatible con futuras versiones de Flet. La migración hacia el uso de `page.window` y `page.overlay` es fundamental para el desarrollo moderno con esta librería.
