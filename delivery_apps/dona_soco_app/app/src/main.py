import os
import sys

# --- SOLUCIÓN TOTAL PARA ANDROID ---
# Forzamos al sistema a ver la raíz de la app y sus subcarpetas
try:
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    if APP_ROOT not in sys.path:
        sys.path.insert(0, APP_ROOT)
    
    # Añadimos explícitamente el directorio padre por si acaso
    PARENT_DIR = os.path.dirname(APP_ROOT)
    if PARENT_DIR not in sys.path:
        sys.path.insert(1, PARENT_DIR)
except Exception as e:
    pass
# -----------------------------------

import flet as ft
from config import APP_NAME

def main(page: ft.Page):
    print("INITIAL ROUTE:", page.route)
    # --- PANTALLA DE CARGA INICIAL ---
    loading_screen = ft.Column(
        [
            ft.ProgressRing(color=ft.Colors.ORANGE),
            ft.Text(f"Cargando {APP_NAME} ...", size=16, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Text("Esto puede tardar unos segundos la primera vez", size=12, color=ft.Colors.GREY_700)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    page.add(loading_screen)
    page.update()

    # --- IMPORTACIONES LOCALES (Optimizan el arranque) ---
    import os
    from flet_core import Audio
    from database import crear_tablas, verificar_admin_login
    from app_views.carrito import create_carrito_view
    from app_views.seguimiento import seguimiento_view
    from app_views.menu import cargar_menu
    from app_views.checkout import create_checkout_view
    from components.notifier import init_pubsub, show_notification
    from panel_restaurante.admin_panel import create_admin_panel_view
    from components.cart import Cart

    crear_tablas()

    if not hasattr(page.session, "cart"):
        page.session.cart = Cart()

    page.title = APP_NAME
    page.window_favicon_path = "favicon.png" # Mantener favicon.png (ya optimizado)
    page.favicon = "favicon.png"

    # --- CONFIGURACIÓN DE PÁGINA ---
    page.theme_mode = ft.ThemeMode.LIGHT
    # ... (resto de la configuración de tema igual)

    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
    
    if "ANDROID_ARGUMENT" in os.environ:
        page.upload_dir = os.path.join(os.path.expanduser("~"), "dona_soco_uploads")
    else:
        page.upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        
    os.makedirs(page.upload_dir, exist_ok=True)
    pubsub = init_pubsub(page)

    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.theme = ft.Theme(
        color_scheme_seed="orange",
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.ORANGE_300,
            on_primary=ft.Colors.WHITE,
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK,
            outline=ft.Colors.ORANGE_200,
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

    admin_mode = False

    def show_snackbar(message: str, color=ft.Colors.BLACK):
        show_notification(page, message, color)

    def close_dialog():
        dialog.open = False
        page.update()

    content_area = ft.Container(expand=True)
    
    def global_file_picker_handler(e):
        if not e.files:
            return
        ctx = getattr(page.session, "file_picker_ctx", None)
        if not ctx:
            return
        try:
            # Si el callback es corrutina, lo ejecutamos con run_task
            import inspect
            if inspect.iscoroutinefunction(ctx["callback"]):
                page.run_task(ctx["callback"], e.files[0])
            else:
                ctx["callback"](e.files[0])
        except Exception as ex:
            print(f"Error callback: {ex}")

    global_file_picker = ft.FilePicker()
    global_file_picker.on_result = global_file_picker_handler
    # Contenedor protector para evitar el error "Unknown control: FilePicker"
    page.overlay.append(ft.Container(content=global_file_picker, width=1, height=1, opacity=0))
    page.session.file_picker = global_file_picker

    export_file_picker = ft.FilePicker()
    page.overlay.append(ft.Container(content=export_file_picker, width=1, height=1, opacity=0))
    
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

    async def logout(e=None):
        nonlocal admin_mode
        admin_mode = False
        show_snackbar("Sesión de administrador cerrada")
        # No limpiamos todo el overlay para no perder los FilePickers globales
        dialog.open = False
        await page.push_route("/menu")
        page.update()

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
                if page.route.startswith("/carrito"):
                    nav.selected_index = 1
                elif page.route.startswith("/seguimiento"):
                    nav.selected_index = 2
                else:
                    nav.selected_index = 0
                show_snackbar("Acceso restringido")
        page.update()

    async def handle_route_change(e):
        print("ROUTE EVENT:", e.route)
        route = e.route
        # --- SISTEMA DE REDIRECCIONAMIENTO (ShortLinks) ---
        route_clean = route.split("?")[0].rstrip("/")

        if route_clean in ["/apk", "/app", "/download"]:
            content_area.content = ft.Column(
                [
                    ft.ProgressRing(),
                    ft.Text("Redirigiendo a la descarga...", size=16, weight="bold"),
                    ft.Text("Si la descarga no inicia automáticamente, pulsa el botón de abajo."),
                    ft.ElevatedButton(
                        "Descargar Manualmente",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda _: page.launch_url(getattr(page.session, "last_dest_url", ""))
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
            page.update()

            import httpx
            from config import API_URL, HEADERS

            code = route_clean.lstrip("/")

            try:
                async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
                    r = await client.get(f"{API_URL}/shortlinks/resolve/{code}")

                    if r.status_code == 200:
                        dest_url = r.json().get("url")

                        if dest_url:
                            page.session.last_dest_url = dest_url
                            await page.launch_url(dest_url)
                            return  
                    else:
                        print("Status no 200:", r.status_code)
            except Exception as ex:
                print(f"Error redireccionando {code}: {ex}")
                show_snackbar("Error al obtener el enlace")

            # Si falla, mostramos error y no seguimos renderizando el menú
            content_area.content = ft.Column(
                [
                    ft.Text("No se pudo resolver el enlace.", weight="bold"),
                    ft.ElevatedButton("Ir al menú", on_click=lambda _: page.go("/menu"))
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
            page.update()
            return

        if route.startswith("/seguimiento"):
            nav.selected_index = 2
            content_area.content = seguimiento_view(page, export_file_picker)
        elif route.startswith("/carrito"):
            nav.selected_index = 1
            content_area.content = create_carrito_view(page, show_snackbar, nav)
        elif route.startswith("/checkout"):
            nav.selected_index = 1
            content_area.content = create_checkout_view(page, show_snackbar, nav)
        elif route.startswith("/admin"):
            if admin_mode:
                # Los pickers ya están en el overlay global de la página
                nav.selected_index = 3
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
    # Forzar procesamiento de la ruta inicial (útil para links directos como /apk)
    page.go(page.route)

    # --- FETCH CONFIG PARA BOTONES SOCIALES ---
    from database import get_configuracion
    import json
    config_header = get_configuracion()
    contactos_header = {}
    if config_header and 'contactos' in config_header:
        try:
            contactos_header = json.loads(config_header['contactos'])
        except:
            pass

    def create_social_menu():
        async def launch_social_url(url):
            await page.launch_url(url)

        menu_items = []
        
        # WhatsApp
        wa = contactos_header.get("whatsapp")
        if wa:
            link_wa = f"https://wa.me/{wa}" if not wa.startswith("http") else wa
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text("WhatsApp"), 
                    icon=ft.Icons.CHAT_BUBBLE_OUTLINE, 
                    on_click=lambda _: page.run_task(launch_social_url, link_wa)
                )
            )
        
        # Facebook
        fb = contactos_header.get("facebook")
        if fb:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text("Facebook"), 
                    icon=ft.Icons.FACEBOOK, 
                    on_click=lambda _: page.run_task(launch_social_url, fb)
                )
            )
        
        # Instagram
        insta = contactos_header.get("instagram")
        if insta:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text("Instagram"), 
                    icon=ft.Icons.CAMERA_ALT, 
                    on_click=lambda _: page.run_task(launch_social_url, insta)
                )
            )

        # X (Twitter)
        x_url = contactos_header.get("x")
        if x_url:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text("X (Twitter)"), 
                    icon=ft.Icons.SHARE, 
                    on_click=lambda _: page.run_task(launch_social_url, x_url)
                )
            )
            
        return ft.PopupMenuButton(
            items=menu_items,
            icon=ft.Icons.MORE_VERT,
            icon_color=ft.Colors.BLACK,
            tooltip="Redes Sociales"
        ) if menu_items else ft.Container()

    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Image(src="icon.png", width=35, height=35),
                    on_click=activar_admin,
                    ink=True,
                    border_radius=18
                ),
                ft.Container(
                    content=ft.Text(APP_NAME, size=18, weight="bold", color=ft.Colors.BLACK, overflow=ft.TextOverflow.ELLIPSIS),
                    alignment=ft.alignment.Alignment(0, 0),
                    expand=True,
                    on_click=activar_admin,
                    padding=ft.Padding.symmetric(horizontal=10)
                ),
                create_social_menu()
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.only(left=10, right=5, top=5, bottom=5),
        bgcolor=ft.Colors.ORANGE_100,
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.BLACK_12))
    )

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.RESTAURANT_MENU, label="Menú"),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART, label="Carrito"),
            ft.NavigationBarDestination(icon=ft.Icons.LOCAL_SHIPPING, label="Seguimiento"),
            ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS, label="Admin"),
        ],
        on_change=change_page
    )

    content_area.content = cargar_menu(page)

    # --- FUNCIÓN DE DESCARGA WEB (ROBUSTA) ---
    def web_download(filename, content_base64):
        page.run_javascript(f"""
            var link = document.createElement('a');
            link.href = 'data:application/octet-stream;base64,{content_base64}';
            link.download = '{filename}';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        """)
    page.session.web_download = web_download

    # --- QUITAR PANTALLA DE CARGA Y MOSTRAR APP ---
    page.clean()
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


if __name__ == "__main__":
    assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
    os.environ["FLET_SECRET_KEY"] = "ads2025_dona_soco_secret"
    # Inicio de la aplicación con ft.run y renderer canvaskit para máxima compatibilidad
    ft.run(main, assets_dir=assets_path, view=ft.AppView.FLET_APP, web_renderer="canvaskit")
