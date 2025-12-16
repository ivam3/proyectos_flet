# app/src/views/menu.py
import flet as ft
from database import obtener_menu, get_configuracion

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
            # Si no hay platillos, mostrar horario de atención
            config = get_configuracion()
            horario = config['horario'] if config else "No disponible"
            
            menu_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.INFO_OUTLINE, size=48, color=ft.Colors.GREY_500),
                            ft.Text(
                                "No hay platillos disponibles por el momento.",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                f"Nuestro horario de atención es: {horario}",
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for platillo in platillos:
                pid, nombre, descripcion, precio, imagen, _ = platillo

                def _on_add_clicked(e, item_id=pid, name=nombre, price=precio):
                    user_cart.add_item(item_id, name, price)
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"'{name}' agregado al carrito"),
                        bgcolor=ft.Colors.GREEN_700,
                    )
                    page.snack_bar.open = True
                    page.update()
                
                menu_list.controls.append(
                    ft.Card(
                        ft.Container(
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Image(src=f"/{imagen}", width=page.width - 40, fit="contain"),
                                    ft.Text(nombre, size=36, weight=ft.FontWeight.BOLD),
                                    ft.Text(descripcion or "Sin descripción", size=24),
                                    ft.Row(
                                        [
                                            ft.Text(f"${precio:.2f}", color=ft.Colors.GREY_700, size=36, weight=ft.FontWeight.BOLD, expand=True),
                                            ft.FilledButton(
                                                "Agregar",
                                                icon="add_shopping_cart",
                                                on_click=_on_add_clicked
                                            )
                                        ],
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    )
                                ]
                            ),
                            padding=12,
                            border_radius=12,
                            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
                        )
                    )
                )
        page.update()

    def handle_search_change(e):
        update_menu_list(e.control.value)

    search_bar = ft.TextField(
        label="Buscar platillo...",
        prefix_icon="search",
        on_change=handle_search_change,
        border_radius=20,
        filled=True,
    )

    # Carga inicial del menú
    update_menu_list()

    return ft.Column(
        expand=True,
        controls=[
            ft.Container(
                content=search_bar,
                padding=ft.Padding.only(left=15, right=15, top=10)
            ),
            menu_list
        ]
    )

