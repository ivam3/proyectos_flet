import flet as ft
import os
from database import crear_tablas, verificar_admin_login
from views.carrito import create_carrito_view
from views.seguimiento import seguimiento_view
from views.menu import cargar_menu
from views.checkout import create_checkout_view
from components.notifier import init_pubsub
from panel_restaurante.admin_panel import create_admin_panel_view
from components.cart import Cart


def main(page: ft.Page):
    crear_tablas()

    # Initialize cart
    if not hasattr(page.session, "cart"):
        page.session.cart = Cart()
    # -------------------------------------------
    
    # ------- PERMISOS ANDROID -------
    # Se ha eliminado PermissionHandler por incompatibilidad técnica en esta versión de Flet.
    # Los permisos necesarios (fotos/notificaciones) serán gestionados automáticamente por el SO.

    page.title = "Antojitos Doña Soco"
    page.window_favicon_path = "favicon.png"
    page.favicon = "favicon.png"  # <- FAVICON WEB USANDO PNG CONVERTIDO

    # Directorio correcto para assets (Flet sirve desde aquí - Read Only)
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
    
    # Directorio para subidas (Debe ser escribible)
    if "ANDROID_ARGUMENT" in os.environ:
        page.upload_dir = os.path.join(os.path.expanduser("~"), "dona_soco_uploads")
    else:
        page.upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        
    os.makedirs(page.upload_dir, exist_ok=True)
    # Sistema pub-sub
    pubsub = init_pubsub(page)

    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Define a custom text theme with slightly smaller font sizes AND FORCE BLACK COLOR
    page.theme = ft.Theme(
        color_scheme_seed="orange",
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.ORANGE_300, # Suavizado de ORANGE a ORANGE_300 para bordes con foco
            on_primary=ft.Colors.WHITE,
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK, # Texto negro por defecto
            outline=ft.Colors.ORANGE_200, # Color de bordes en reposo
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(size=15, color=ft.Colors.BLACK),
            body_medium=ft.TextStyle(size=13, color=ft.Colors.BLACK),
            body_small=ft.TextStyle(size=11, color=ft.Colors.BLACK),
            title_large=ft.TextStyle(size=20, color=ft.Colors.BLACK),
            title_medium=ft.TextStyle(size=15, color=ft.Colors.BLACK),
            title_small=ft.TextStyle(size=13, color=ft.Colors.BLACK),
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
            margin=ft.Margin.only(bottom=50, left=10, right=10), # Margen reducido
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    def close_dialog():
        dialog.open = False
        page.update()

    # Área central de contenido
    content_area = ft.Container(expand=True)
    
    # ------- DIÁLOGO DE ADMIN & FILE PICKER GLOBAL -------
    # --- SELECTOR GLOBAL ESTABLE (SOLUCIÓN CICLO DE VIDA) ---
    def global_file_picker_handler(e):
        print(f"GLOBAL PICKER RESULT: {e.files}")
        if not e.files:
            return

        # Recuperamos datos persistentes de forma segura
        ctx = getattr(page.session, "file_picker_ctx", None)
        if not ctx:
            print("No picker context found in session")
            return

        # Ejecutamos callback seguro
        try:
            # El callback espera el objeto file directo, según el snippet del usuario
            ctx["callback"](e.files[0])
        except Exception as ex:
            print(f"Error executing picker callback: {ex}")

    global_file_picker = ft.FilePicker()
    global_file_picker.on_result = global_file_picker_handler
    # Wrap in invisible container to hide visual glitches in Android (Red Stripe fix)
    page.overlay.append(ft.Container(content=global_file_picker, visible=False))
    page.session.file_picker = global_file_picker

    # --- SELECTOR DE EXPORTACIÓN (PEDIDOS) ---
    # Instanciamos aquí para evitar errores visuales y duplicados
    export_file_picker = ft.FilePicker()
    page.overlay.append(ft.Container(content=export_file_picker, visible=False))

    # ------- DIÁLOGO DE ADMIN -------
    admin_field = ft.TextField(password=True, hint_text="Clave")

    def activar_admin(e):
        dialog.open = True
        page.update()

    async def validar_clave(e=None):
        nonlocal admin_mode
        clave = admin_field.value.strip()
        if verificar_admin_login(clave):
            admin_mode = True
            close_dialog()
            show_snackbar("Modo administrador activado")
            
            # Sincronizar vía ruteo
            await page.push_route("/admin")
        else:
            admin_field.value = ""
            show_snackbar("Acceso restringido")
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Ingrese clave de administrador"),
        content=admin_field,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: close_dialog(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700)),
            ft.TextButton("Aceptar", on_click=validar_clave, style=ft.ButtonStyle(color=ft.Colors.BROWN_700)),
        ],
    )
    page.overlay.append(dialog)

    # ------- LOGOUT -------
    async def logout(e=None):
        nonlocal admin_mode
        admin_mode = False
        show_snackbar("Sesión de administrador cerrada")
        # Restore overlay state (dialog only, picker is in main controls)
        page.overlay.clear()
        page.overlay.append(dialog)
        await page.push_route("/menu")
        page.update()

    # ------- CAMBIAR PANTALLAS -------
    async def change_page(e):
        selected = e.control.selected_index
        if selected == 0:
            await page.push_route("/menu")
        elif selected == 1:
            await page.push_route("/carrito")
        elif selected == 2:
            await page.push_route("/seguimiento")
        elif selected == 3:
            if admin_mode:
                await page.push_route("/admin")
            else:
                # Si no es admin, forzar el índice a la vista actual
                if page.route.startswith("/carrito"):
                    nav.selected_index = 1
                elif page.route.startswith("/seguimiento"):
                    nav.selected_index = 2
                else:
                    nav.selected_index = 0
                show_snackbar("Acceso restringido")
        page.update()

    # ------- ROUTING -------
    async def handle_route_change(e):
        route = e.route
        if route.startswith("/seguimiento"):
            nav.selected_index = 2
            content_area.content = seguimiento_view(page)
        elif route.startswith("/carrito"):
            nav.selected_index = 1
            content_area.content = create_carrito_view(page, show_snackbar, nav)
        elif route.startswith("/checkout"):
            nav.selected_index = 1
            content_area.content = create_checkout_view(page, show_snackbar, nav)
        elif route.startswith("/admin"):
            if admin_mode:
                nav.selected_index = 3
                # Usamos el export_file_picker ya creado en el inicio
                content_area.content = create_admin_panel_view(
                    page, 
                    logout_func=logout, 
                    file_picker=global_file_picker,
                    export_file_picker=export_file_picker
                )
            else:
                await page.push_route("/menu")
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

    # Usar SafeArea para evitar solapamiento con la barra de estado
    page.add(
        ft.SafeArea(
            ft.Column(
                [
                    top_bar,
                    content_area,
                    nav,
                ],
                expand=True,
                spacing=0
            ),
            expand=True
        )
    )


# Ruta absoluta segura para assets
assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
os.environ["FLET_SECRET_KEY"] = "ads2025_dona_soco_secret"
ft.run(main, assets_dir=assets_path, view=ft.AppView.FLET_APP, web_renderer="canvaskit")
