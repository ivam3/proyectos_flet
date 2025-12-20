import flet as ft
from .views.menu_admin import menu_admin_view
from .views.pedidos import pedidos_view
from .views.configuracion import configuracion_view # Importar la nueva vista

def create_admin_panel_view(page: ft.Page, logout_func, file_picker):
    """
    Crea la vista del panel de administración utilizando una fila de botones
    para cambiar entre las vistas de gestión.
    """

    # Se crean las vistas de contenido una sola vez
    menu_view = menu_admin_view(page, file_picker)
    pedidos_view_content = pedidos_view(page, file_picker)
    config_view = configuracion_view(page) # Instanciar la vista de configuración

    # Contenedor donde se mostrará la vista de menú o pedidos
    admin_content_area = ft.Container(
        content=menu_view, # Cargar vista de menú por defecto
        expand=True,
    )

    # Funciones para cambiar el contenido
    def show_menu_view(e):
        admin_content_area.content = menu_view
        admin_content_area.update()

    def show_pedidos_view(e):
        admin_content_area.content = pedidos_view_content
        admin_content_area.update()

    def show_config_view(e): # Función para mostrar la vista de configuración
        admin_content_area.content = config_view
        admin_content_area.update()

    # Layout de la vista del panel de administración
    admin_panel_layout = ft.Column(
        controls=[
            # Header
            ft.Row(
                [
                    ft.Text("Centro de Administración", size=18, weight="bold", expand=True, text_align=ft.TextAlign.CENTER),
                    ft.TextButton(content=ft.Text("Salir"), on_click=logout_func, tooltip="Cerrar Sesión")
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            ft.Divider(),
            # Botones de navegación
            ft.Row(
                [
                    ft.Button(content=ft.Text("Gestión de Menú"), on_click=show_menu_view, expand=True),
                    ft.Button(content=ft.Text("Gestión de Pedidos"), on_click=show_pedidos_view, expand=True),
                    ft.Button(content=ft.Text("Configuración"), on_click=show_config_view, expand=True), # Nuevo botón
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            # Área de contenido dinámico
            admin_content_area,
        ],
        expand=True,
    )

    return admin_panel_layout