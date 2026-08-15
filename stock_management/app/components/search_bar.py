import flet as ft

def search_bar(page: ft.Page, on_search):
    
    def handle_search(_):
        on_search(search_input.value)

    search_input = ft.TextField(
        hint_text="Buscar modelo, SKU, talla...",
        expand=True,
        height=45,
        text_size=14,
        content_padding=10,
        border_color=ft.Colors.ORANGE_400,
        border_width=2,
        border_radius=10,
        on_submit=handle_search
    )

    return ft.Row(
        [
            search_input,
            ft.IconButton(
                icon=ft.Icons.SEARCH,
                icon_color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLACK,
                on_click=handle_search,
                tooltip="Buscar"
            ),
        ],
        spacing=5,
        expand=True # Permite que el buscador tome el espacio disponible sin empujar otros elementos
    )
