import flet as ft
from components.product_form import product_form

def register_view(page: ft.Page):
    
    def on_success():
        page.snack_bar = ft.SnackBar(ft.Text("Registro exitoso"), bgcolor=ft.Colors.GREEN)
        page.snack_bar.open = True
        page.update()

    # Estructura homologada y segura para Android/Termux
    return ft.Column(
        [
            ft.Text("Registro de Mercancía", size=26, weight="bold", color=ft.Colors.BLACK),
            ft.Text("Completa el formulario para añadir stock.", color=ft.Colors.GREY_700),
            ft.Divider(),
            # Usamos MainAxisAlignment para el posicionamiento en lugar de ft.alignment
            ft.Column(
                [product_form(page, on_success=on_success)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=float("inf")
            )
        ],
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
        spacing=10
    )
