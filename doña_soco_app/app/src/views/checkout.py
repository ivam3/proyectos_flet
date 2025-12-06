# src/views/checkout.py
import flet as ft
from components import cart
from database import guardar_pedido
from views.menu import cargar_menu

def create_checkout_view(page: ft.Page, show_snackbar):
    """Pantalla donde el usuario ingresa sus datos de envío antes de confirmar el pedido."""

    nombre_field = ft.TextField(label="Nombre completo", autofocus=True, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    telefono_field = ft.TextField(label="Teléfono de contacto", keyboard_type=ft.KeyboardType.PHONE, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    direccion_field = ft.TextField(label="Dirección completa", multiline=True, max_lines=3, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    referencias_field = ft.TextField(label="Referencias (opcional)", multiline=True, max_lines=2, label_style=ft.TextStyle(color=ft.Colors.BLACK))

    total = cart.get_total()
    dialog = ft.AlertDialog()

    def _volver_al_menu(e):
        """Vuelve al menú principal y limpia el carrito."""
        cart.clear_cart()
        dialog.open = False
        page.controls[1].content = cargar_menu(page)
        page.update()

    def confirmar_pedido(e):
        # Validación simple
        if not nombre_field.value.strip() or not telefono_field.value.strip() or not direccion_field.value.strip():
            show_snackbar("Por favor completa todos los campos obligatorios ❗")
            return

        nombre = nombre_field.value.strip()
        telefono = telefono_field.value.strip()
        direccion = direccion_field.value.strip()
        referencias = referencias_field.value.strip()
        items = cart.get_items()
        page.client_storage.set("telefono_cliente", telefono)
        exito = guardar_pedido(nombre, telefono, direccion, referencias, total, items)

        if exito:
            dialog.title = ft.Text("Pedido registrado ✅", color=ft.Colors.BLACK)
            dialog.content = ft.Text("Tu pedido ha sido enviado correctamente.\nRecibirás notificaciones del estado.", color=ft.Colors.BLACK)
            dialog.actions = [ft.TextButton("Aceptar", on_click=_volver_al_menu)]
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
            direccion_field,
            referencias_field,
            ft.Divider(),
            ft.Text(f"Total a pagar: ${total:.2f}", size=20, weight="bold", color=ft.Colors.BLACK),
            ft.ElevatedButton("Confirmar pedido", on_click=confirmar_pedido)
        ],
        scroll="auto",
        expand=True
    )
