import flet as ft
from config import API_URL

def photo_viewer(page: ft.Page, product, refresh_callback):
    """Diálogo modal para visualizar y gestionar las fotos de un producto."""
    
    photos = product.get('photos', [])
    if not photos:
        page.snack_bar = ft.SnackBar(ft.Text("Este producto no tiene fotos"))
        page.snack_bar.open = True
        page.update()
        return

    current_idx = 0
    
    # Controles de la UI
    img_display = ft.Image(
        src=f"{API_URL}/photos/{photos[current_idx]['file_path']}",
        width=400, height=400, fit="contain"
    )
    
    counter_text = ft.Text(f"Foto {current_idx + 1} / {len(photos)}", weight="bold")

    def update_viewer():
        nonlocal current_idx
        img_display.src = f"{API_URL}/photos/{photos[current_idx]['file_path']}"
        counter_text.value = f"Foto {current_idx + 1} / {len(photos)}"
        page.update()

    def on_next(e):
        nonlocal current_idx
        current_idx = (current_idx + 1) % len(photos)
        update_viewer()

    def on_prev(e):
        nonlocal current_idx
        current_idx = (current_idx - 1) % len(photos)
        update_viewer()

    def on_delete_photo(e):
        api = page.session.api
        photo_id = photos[current_idx]['id']
        if api.delete_photo(photo_id):
            page.snack_bar = ft.SnackBar(ft.Text("Foto eliminada"), bgcolor=ft.Colors.GREEN)
            page.snack_bar.open = True
            # Cerramos el visor y refrescamos la tabla principal
            dlg.open = False
            page.update()
            refresh_callback()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar foto"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    # Botones de navegación (estilo HTML original)
    btn_prev = ft.IconButton(ft.Icons.NAVIGATE_BEFORE, on_click=on_prev, bgcolor=ft.Colors.BLACK12)
    btn_next = ft.IconButton(ft.Icons.NAVIGATE_NEXT, on_click=on_next, bgcolor=ft.Colors.BLACK12)

    dlg = ft.AlertDialog(
        title=ft.Text(f"Galería: {product['model_name']}"),
        content=ft.Column(
            [
                ft.Stack(
                    [
                        ft.Container(content=ft.Row([img_display], alignment=ft.MainAxisAlignment.CENTER), width=400, height=400),
                        ft.Container(content=ft.Row([btn_prev], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER), width=400, height=400),
                        ft.Container(content=ft.Row([btn_next], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER), width=400, height=400),
                    ],
                    width=400, height=400
                ),
                ft.Row(
                    [
                        counter_text,
                        ft.Button(
                            "Eliminar Foto",
                            icon=ft.Icons.DELETE_FOREVER,
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.RED_700,
                            on_click=on_delete_photo
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            ],
            tight=True,
            spacing=20
        ),
        actions=[
            ft.TextButton("Cerrar", on_click=lambda _: (setattr(dlg, "open", False), page.update()))
        ]
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()
