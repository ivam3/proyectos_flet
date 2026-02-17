import flet as ft
from components.notifier import show_notification

def create_admin_panel_view(page: ft.Page, logout_func, file_picker, export_file_picker=None):
    """
    Crea la vista del panel de administración utilizando carga perezosa (Lazy Loading)
    para mejorar radicalmente la velocidad de respuesta inicial.
    """

    # Contenedor principal de contenido
    admin_content_area = ft.Container(expand=True)
    
    # Cache de vistas para evitar recargas innecesarias al swichear entre ellas
    views_cache = {}

    def get_or_create_view(view_type):
        if view_type not in views_cache:
            show_notification(page, "Cargando sección...", ft.Colors.BLUE_GREY_700)
            if view_type == "menu":
                from .admin_views.menu_admin import menu_admin_view
                views_cache[view_type] = menu_admin_view(page, file_picker)
            elif view_type == "pedidos":
                from .admin_views.pedidos import pedidos_view
                views_cache[view_type] = pedidos_view(page, export_file_picker)
            elif view_type == "config":
                from .admin_views.configuracion import configuracion_view
                views_cache[view_type] = configuracion_view(page)
        return views_cache[view_type]

    # Funciones para cambiar el contenido
    def show_menu_view(e):
        admin_content_area.content = get_or_create_view("menu")
        admin_content_area.update()

    def show_pedidos_view(e):
        admin_content_area.content = get_or_create_view("pedidos")
        admin_content_area.update()

    def show_config_view(e):
        admin_content_area.content = get_or_create_view("config")
        admin_content_area.update()

    # Cargar vista inicial (Menú) de forma diferida
    # Usamos un pequeño delay para permitir que el marco del panel se pinte primero
    def initial_load():
        admin_content_area.content = get_or_create_view("menu")
        admin_content_area.update()
    
    import threading
    import time
    threading.Timer(0.1, initial_load).start()

    # Layout de la vista del panel de administración
    admin_panel_layout = ft.Column(
        controls=[
            # Header
            ft.Row(
                [
                    ft.Text("Centro de Administración", size=18, weight="bold", expand=True, text_align=ft.TextAlign.CENTER, color=ft.Colors.BLACK),
                    ft.TextButton(content=ft.Text("Salir"), on_click=logout_func, tooltip="Cerrar Sesión")
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            ft.Divider(),
            # Botones de navegación
            ft.Row(
                [
                    ft.Button(content=ft.Text("Gestión de Menú"), on_click=show_menu_view, color=ft.Colors.BROWN, expand=True),
                    ft.Button(content=ft.Text("Gestión de Pedidos"), on_click=show_pedidos_view, color=ft.Colors.BROWN, expand=True),
                    ft.Button(content=ft.Text("Configuración"), on_click=show_config_view, color=ft.Colors.BROWN, expand=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            # Área de contenido dinámico
            admin_content_area,
        ],
        expand=True,
    )

    return admin_panel_layout
