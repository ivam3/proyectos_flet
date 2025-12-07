# src/views/checkout.py
import flet as ft
from components import cart
from database import guardar_pedido
from views.menu import cargar_menu

from views.seguimiento import seguimiento_view

def create_checkout_view(page: ft.Page, show_snackbar, nav):
    """Pantalla donde el usuario ingresa sus datos de envío antes de confirmar el pedido."""
    import re

    # --- CAMPOS DEL FORMULARIO ---
    nombre_field = ft.TextField(label="Nombre completo", autofocus=True, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    telefono_field = ft.TextField(label="Teléfono de contacto", keyboard_type=ft.KeyboardType.PHONE, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    
    # Campos de dirección desglosados
    calle_field = ft.TextField(label="Calle", label_style=ft.TextStyle(color=ft.Colors.BLACK))
    numero_field = ft.TextField(label="Número (ext e int)", label_style=ft.TextStyle(color=ft.Colors.BLACK))
    ciudad_field = ft.TextField(label="Ciudad", label_style=ft.TextStyle(color=ft.Colors.BLACK))
    cp_field = ft.TextField(label="Código Postal", keyboard_type=ft.KeyboardType.NUMBER, max_length=5, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    estado_field = ft.TextField(label="Estado", label_style=ft.TextStyle(color=ft.Colors.BLACK))

    referencias_field = ft.TextField(label="Referencias (opcional)", multiline=True, max_lines=2, label_style=ft.TextStyle(color=ft.Colors.BLACK))

    total = cart.get_total()
    dialog = ft.AlertDialog()

    def _ir_a_seguimiento(e):
        """Redirige a la pantalla de seguimiento y limpia el carrito."""
        from views.seguimiento import seguimiento_view
        cart.clear_cart()
        dialog.open = False
        page.controls[1].content = seguimiento_view(page) # Carga la vista de seguimiento
        nav.selected_index = 2 # Actualiza el nav bar
        page.update()

    def validar_campos():
        """Valida todos los campos obligatorios y sus formatos."""
        campos = {
            "Nombre": nombre_field, "Teléfono": telefono_field,
            "Calle": calle_field, "Número": numero_field,
            "Ciudad": ciudad_field, "Código Postal": cp_field, "Estado": estado_field
        }
        for nombre, campo in campos.items():
            if not campo.value or not campo.value.strip():
                show_snackbar(f"El campo '{nombre}' es obligatorio.")
                return False

        # Validar CP
        if not re.match(r"^\d{5}$", cp_field.value.strip()):
            show_snackbar("El Código Postal debe tener 5 dígitos numéricos.")
            return False
            
        # Validar longitud y caracteres (ejemplo simple)
        for nombre, campo in {"Calle": calle_field, "Ciudad": ciudad_field, "Estado": estado_field}.items():
            if not re.match(r"^[a-zA-Z0-9\s.,-]*$", campo.value.strip()):
                show_snackbar(f"El campo '{nombre}' contiene caracteres no permitidos.")
                return False
            if len(campo.value.strip()) > 100:
                show_snackbar(f"El campo '{nombre}' es demasiado largo.")
                return False

        return True


    def confirmar_pedido(e):
        if not validar_campos():
            return

        # Unir dirección para guardarla
        direccion_completa = (
            f"{calle_field.value.strip()}, "
            f"{numero_field.value.strip()}, "
            f"{ciudad_field.value.strip()}, "
            f"{estado_field.value.strip()}, "
            f"C.P. {cp_field.value.strip()}"
        )

        nombre = nombre_field.value.strip()
        telefono = telefono_field.value.strip()
        referencias = referencias_field.value.strip()
        items = cart.get_items()
        
        page.client_storage.set("telefono_cliente", telefono)
        
        exito, codigo_seguimiento = guardar_pedido(nombre, telefono, direccion_completa, referencias, total, items)

        if exito:
            dialog.title = ft.Text("Pedido registrado ✅", color=ft.Colors.BLACK)
            dialog.content = ft.Column([
                ft.Text("Tu pedido ha sido enviado correctamente.", color=ft.Colors.BLACK),
                ft.Text("Usa este código para darle seguimiento:", color=ft.Colors.BLACK),
                ft.Text(f"{codigo_seguimiento}", weight="bold", size=20, selectable=True, color=ft.Colors.BLACK),
                ft.Text("Guárdalo bien, lo necesitarás para consultar el estado.", color=ft.Colors.BLACK, italic=True)
            ])
            dialog.actions = [ft.TextButton("Aceptar", on_click=_ir_a_seguimiento)]
        else:
            dialog.title = ft.Text("Error ❌", color=ft.Colors.BLACK)
            dialog.content = ft.Text("Ocurrió un error al guardar el pedido. Intenta nuevamente.", color=ft.Colors.BLACK)
            dialog.actions = [ft.TextButton("Cerrar", on_click=lambda e: (setattr(dialog, 'open', False), page.update()))]

        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    return ft.Column(
        [
            ft.Text("Datos de entrega", size=24, weight="bold", color=ft.Colors.BLACK),
            ft.Divider(),
            nombre_field,
            telefono_field,
            calle_field,
            numero_field,
            ciudad_field,
            cp_field,
            estado_field,
            referencias_field,
            ft.Divider(),
            ft.Text(f"Total a pagar: ${total:.2f}", size=20, weight="bold", color=ft.Colors.BLACK),
            ft.ElevatedButton("Confirmar pedido", on_click=confirmar_pedido)
        ],
        scroll="auto",
        expand=True
    )
