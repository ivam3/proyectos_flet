import flet as ft
import os
from database import crear_tablas
from views.carrito import create_carrito_view
from views.seguimiento import seguimiento_view
from views.menu import cargar_menu
from components.notifier import init_pubsub
from panel_restaurante.admin_panel import create_admin_panel_view
from components.cart import Cart


def main(page: ft.Page):
    crear_tablas()

    # Initialize cart
    if not hasattr(page.session, "cart"):
        page.session.cart = Cart()
    # -------------------------------------------

    page.title = "Antojitos Doña Soco"
    page.window_favicon_path = "icon.png"  # <- FAVICON

    # Directorio correcto para assets (Flet sirve desde aquí)
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
    page.upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
    os.makedirs(page.upload_dir, exist_ok=True)
    # Sistema pub-sub
    pubsub = init_pubsub(page)

    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Define a custom text theme with slightly smaller font sizes
    page.theme = ft.Theme(
        color_scheme_seed="orange",
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(size=15),
            body_medium=ft.TextStyle(size=13),
            body_small=ft.TextStyle(size=11),
            title_large=ft.TextStyle(size=20),
            title_medium=ft.TextStyle(size=15),
            title_small=ft.TextStyle(size=13),
        )
    )
    page.window.width = 400
    page.window.height = 700

    # ------- ESTADO -------
    admin_mode = False

    # ------- UTILIDADES -------
    def show_snackbar(text):
        snack_bar = ft.SnackBar(ft.Text(text))
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()

    def close_dialog():
        dialog.open = False
        page.update()

    # Área central de contenido
    content_area = ft.Container(expand=True)
    
    # ------- LOGOUT -------
    def logout(e=None):
        nonlocal admin_mode
        admin_mode = False
        content_area.content = cargar_menu(page)
        show_snackbar("Sesión de administrador cerrada")
        page.update()

    # ------- CAMBIAR PANTALLAS -------
    def change_page(e):
        selected = e.control.selected_index
        if selected == 0:
            content_area.content = cargar_menu(page)
        elif selected == 1:
            content_area.content = create_carrito_view(page, show_snackbar, nav)
        elif selected == 2:
            content_area.content = seguimiento_view(page)
        elif selected == 3:
            if admin_mode:
                content_area.content = create_admin_panel_view(page, logout_func=logout)
            else:
                show_snackbar("Acceso restringido")
        page.update()

    # ------- DIÁLOGO DE ADMIN -------
    admin_field = ft.TextField(password=True, hint_text="Clave")

    def activar_admin(e):
        dialog.open = True
        page.update()

    def validar_clave(e=None):
        nonlocal admin_mode
        if admin_field.value.strip() == "zz":
            admin_mode = True
            close_dialog()
            show_snackbar("Modo administrador activado")
            content_area.content = create_admin_panel_view(page, logout_func=logout)
        else:
            admin_field.value = ""
            show_snackbar("Clave incorrecta")
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Ingrese clave de administrador"),
        content=admin_field,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: close_dialog()),
            ft.TextButton("Aceptar", on_click=validar_clave),
        ],
    )
    page.overlay.append(dialog)

    # ------- HEADER (doble clic para admin) -------
    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Image(src="icon.png", width=45, height=45),
                ft.Text("Antojitos Doña Soco", size=22, weight="bold", color=ft.Colors.BLACK, expand=True, text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        on_click=activar_admin,
        padding=15,
        bgcolor=ft.Colors.ORANGE_100,
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.BLACK_12))
    )

    # ------- BOTTOM NAV -------
    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.RESTAURANT_MENU, label="Menú"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART, label="Carrito"),
            ft.NavigationBarDestination(icon=ft.Icons.LOCAL_SHIPPING, label="Seguimiento"),
            ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS, label="Admin"),
        ],
        on_change=change_page
    )

    # ------- UI FINAL -------
    content_area.content = cargar_menu(page)

    page.add(
        top_bar,
        content_area,
        nav
    )


# Ruta correcta del assets_dir
ft.run(main, assets_dir="src/assets") #, secret_key="ads2025")
