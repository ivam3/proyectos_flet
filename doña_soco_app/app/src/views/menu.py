# app/src/views/menu.py
import flet as ft
from database import obtener_menu
from components import cart
from components.cart import add_item


def cargar_menu(page: ft.Page):
    """Carga y muestra los platillos del menú."""
    lista = ft.ListView(expand=True, spacing=10, padding=20)

    platillos = obtener_menu(solo_activos=True)

    if not platillos:
        lista.controls.append(ft.Text("No hay platillos registrados aún 🍽️"))
    else:
        for id, nombre, descripcion, precio, imagen, is_active in platillos:

            def _on_add(e, item_id=id, name=nombre, price=precio):
                cart.add_item(item_id, name, price)
                snack_bar = ft.SnackBar(ft.Text(f"{name} agregado al carrito ✅"))
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()

            card_content = [
                ft.Text(nombre, size=20, weight="bold"),
                ft.Text(descripcion or "Sin descripción", size=14),
                ft.Text(f"${precio:.2f}", size=18, weight="bold"),
                ft.ElevatedButton("Agregar al carrito", on_click=_on_add)
            ]

            # <=------------ CORREGIDO AQUI -------------=>
            if imagen:
                card_content.insert(
                    0,
                    ft.Image(
                        src=f"/assets/{imagen}",
                        width=100,
                        height=100,
                        fit=ft.ImageFit.COVER
                    )
                )

            lista.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(card_content)
                    )
                )
            )

    return ft.Container(
        expand=True,
        content=lista
    )
