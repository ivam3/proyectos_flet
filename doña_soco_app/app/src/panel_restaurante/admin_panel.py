import flet as ft
from .views.menu_admin import menu_admin_view
from .views.pedidos import pedidos_view

def create_admin_panel_view(page: ft.Page):
    """
    Crea la vista principal del panel de administración con pestañas de navegación en la parte superior.
    """
    
    admin_content_area = ft.Container(expand=True)

    def switch_admin_view(selected_index):
        if selected_index == 0:
            admin_content_area.content = menu_admin_view(page)
        elif selected_index == 1:
            admin_content_area.content = pedidos_view(page)
        else:
            admin_content_area.content = ft.Text("Selección no válida")
        page.update()

    def tab_change(e):
        switch_admin_view(e.control.selected_index)

    admin_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Gestión de Menú"),
            ft.Tab(text="Gestión de Pedidos"),
        ],
        on_change=tab_change,
        expand=True,
    )

    # Carga inicial de la vista de menú en el panel
    switch_admin_view(0)

    # El control que se devolverá y se insertará en la página principal
    admin_panel_layout = ft.Column(
        [
            admin_tabs,
            admin_content_area,
        ],
        expand=True,
    )

    return admin_panel_layout
