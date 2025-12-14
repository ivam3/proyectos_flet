# app/src/views/menu.py
import flet as ft
from database import obtener_menu


def cargar_menu(page: ft.Page):
    """Carga y muestra los platillos del menú con una barra de búsqueda."""
    
    # Obtener el carrito de la sesión del usuario
    user_cart = page.session.cart

    menu_list = ft.ListView(expand=True, spacing=10, padding=20)

    def update_menu_list(search_term=""):
        """Limpia y recarga la lista de platillos según el término de búsqueda."""
        menu_list.controls.clear()
        platillos = obtener_menu(solo_activos=True, search_term=search_term)

        if not platillos:
            menu_list.controls.append(ft.Text("No se encontraron platillos 🍽️"))
        else:
            for id, nombre, descripcion, precio, imagen, is_active in platillos:
                def _on_add(e, item_id=id, name=nombre, price=precio):
                    # Usar el carrito de la sesión
                    user_cart.add_item(item_id, name, price)
                    snack_bar = ft.SnackBar(ft.Text(f"{name} agregado al carrito ✅"))
                    page.overlay.append(snack_bar)
                    snack_bar.open = True
                    page.update()

                card_content = [
                    ft.Text(nombre, size=20, weight="bold", color=ft.Colors.BLACK),
                    ft.Text(descripcion or "Sin descripción", size=14, color=ft.Colors.BLACK),
                    ft.Text(f"${precio:.2f}", size=18, weight="bold", color=ft.Colors.BLACK),
                    ft.FilledButton("Agregar al carrito", on_click=_on_add)
                ]

                if imagen:
                    card_content.insert(
                        0,
                        ft.Image(
                            src=f"/{imagen}", # Flet espera una ruta relativa a la raíz del servidor de assets
                            width=100,
                            height=100,
                            fit=ft.ImageFit.COVER,
                            border_radius=ft.BorderRadius.all(8)
                        )
                    )

                menu_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column(card_content, spacing=5)
                        )
                    )
                )
        page.update()

    def handle_search_change(e):
        update_menu_list(e.control.value)

    search_field = ft.TextField(
        label="Buscar platillo...",
        prefix_icon=ft.Icons.SEARCH,
        on_change=handle_search_change,
        border_radius=ft.BorderRadius.all(20),
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    # Carga inicial del menú
    update_menu_list()

    return ft.Column(
        expand=True,
        controls=[
            ft.Container(
                content=search_field,
                padding=ft.Padding.only(left=15, right=15, top=10)
            ),
            menu_list
        ]
    )
