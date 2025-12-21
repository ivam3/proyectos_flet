import flet as ft
import os
from database import crear_tablas, verificar_admin_login
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
    page.window_favicon_path = "logo.jpg"  # <- FAVICON

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
    def show_snackbar(message: str, color=ft.Colors.BLACK):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        page.snack_bar.open = True
        page.update()

    def close_dialog():
        dialog.open = False
        page.update()

    # Área central de contenido
    content_area = ft.Container(expand=True)
    
    # ------- DIÁLOGO DE ADMIN & FILE PICKER GLOBAL -------
    admin_field = ft.TextField(password=True, hint_text="Clave")
    
    # Global FilePicker for the whole app session
    global_file_picker = ft.FilePicker()
    # We use a hidden container instead of overlay to avoid the "red stripe" bug on Android
    picker_shield = ft.Container(content=global_file_picker, visible=False)

    def activar_admin(e):
        dialog.open = True
        page.update()

    def validar_clave(e=None):
        nonlocal admin_mode
        clave = admin_field.value.strip()
        if verificar_admin_login(clave):
            admin_mode = True
            close_dialog()
            show_snackbar("Modo administrador activado")
            
            # Abrir panel admin y sincronizar navegación
            nav.selected_index = 3
            content_area.content = create_admin_panel_view(page, logout_func=logout, file_picker=global_file_picker)
            page.update()
        else:
            admin_field.value = ""
            show_snackbar("Acceso restringido")
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

    # ------- LOGOUT -------
    def logout(e=None):
        nonlocal admin_mode
        admin_mode = False
        content_area.content = cargar_menu(page)
        show_snackbar("Sesión de administrador cerrada")
        # Restore overlay state (dialog only, picker is in main controls)
        page.overlay.clear()
        page.overlay.append(dialog)
        nav.selected_index = 0 # Volver al menú
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
                content_area.content = create_admin_panel_view(page, logout_func=logout, file_picker=global_file_picker)
            else:
                show_snackbar("Acceso restringido")
        page.update()

    # ------- ROUTING -------
    def handle_route_change(e):
        route = e.route
        if route.startswith("/seguimiento"):
            nav.selected_index = 2
            content_area.content = seguimiento_view(page)
        elif route.startswith("/carrito"):
            nav.selected_index = 1
            content_area.content = create_carrito_view(page, show_snackbar, nav)
        elif route == "/" or route.startswith("/menu"):
            nav.selected_index = 0
            content_area.content = cargar_menu(page)
        
        page.update()

    page.on_route_change = handle_route_change

    # ------- HEADER (doble clic para admin) -------
    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Image(src="icon.png", width=60, height=60),
                ft.Text("Antojitos Doña Soco", size=22, weight="bold", color=ft.Colors.BLACK, expand=True, text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        on_click=activar_admin,
        ink=True,
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
        nav,
        picker_shield # FilePicker globally available but visually shielded
    )


# Ruta correcta del assets_dir
ft.run(main, assets_dir="src/assets", view=ft.AppView.WEB_BROWSER) #, secret_key="ads2025")
