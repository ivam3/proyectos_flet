import flet as ft
from .views.menu_admin import menu_admin_view
from .views.pedidos import pedidos_view

def create_admin_panel_view(page: ft.Page):
    """
    Crea la vista principal del panel de administración con navegación lateral.
    """
    
    # Contenedor para el contenido principal del panel
    admin_content_area = ft.Container(expand=True)

    def switch_admin_view(selected_index):
        if selected_index == 0:
            admin_content_area.content = menu_admin_view(page)
        elif selected_index == 1:
            admin_content_area.content = pedidos_view(page)
        else:
            admin_content_area.content = ft.Text("Selección no válida")
        page.update()

    def nav_rail_change(e):
        switch_admin_view(e.control.selected_index)

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=False,
        min_width=80,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.RESTAURANT_MENU,
                selected_icon=ft.Icons.RESTAURANT_MENU,
                label="Gestión de Menú",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LIST_ALT,
                selected_icon=ft.Icons.LIST,
                label="Gestión de Pedidos",
            ),
        ],
        on_change=nav_rail_change,
    )

    # Carga inicial de la vista de menú en el panel
    switch_admin_view(0)

    # El control que se devolverá y se insertará en la página principal
    admin_panel_layout = ft.Row(
        [
            nav_rail,
            ft.VerticalDivider(width=1),
            admin_content_area,
        ],
        expand=True,
    )

    return admin_panel_layout
