import flet as ft
from .views.menu_admin import menu_admin_view
from .views.pedidos import pedidos_view

def create_admin_panel_view(page: ft.Page):

    # Área donde se cargan las vistas (este sí debe expandir)
    admin_content_area = ft.Container(
        expand=True,
        padding=0,          # Menos espacio desperdiciado
        margin=0,
        content=None
    )

    # Cambiar el contenido según la pestaña
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

    # Tabs compactos
    admin_tabs = ft.Tabs(
        selected_index=0,
        on_change=tab_change,
        expand=False,
        animation_duration=150,
        height=48,                  # ← Tabs más pequeños
        tab_alignment=ft.TabAlignment.START,
        indicator_color=ft.Colors.BROWN_400,
        divider_color=ft.Colors.BROWN_200,
        tabs=[
            ft.Tab(
                text="Gestión de Menú",
                icon=ft.Icons.RESTAURANT_MENU,
            ),
            ft.Tab(
                text="Gestión de Pedidos",
                icon=ft.Icons.RECEIPT,
            ),
        ],
    )

    # Compactar espacio superior
    header = ft.Container(
        content=ft.Text(
            "Antojitos Doña Soco - Administración",
            size=18,
            weight="bold",
        ),
        alignment=ft.alignment.center,
        padding=10,
        margin=ft.margin.only(bottom=5),
    )

    # Panel completo
    admin_panel_layout = ft.Column(
        expand=True,
        spacing=5,
        controls=[
            header,
            admin_tabs,
            admin_content_area,
        ]
    )

    # Cargar la primera vista
    switch_admin_view(0)

    return admin_panel_layout
