import flet as ft
from components.search_bar import search_bar
from components.inventory_table import inventory_table
from datetime import datetime

def inventory_view(page: ft.Page):
    
    api = page.session.api
    # Contenedor para la tabla (sin fondo para evitar el recuadro gris)
    table_container = ft.Column(
        width=float("inf"),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def refresh_table(search_term=None):
        table_container.controls.clear()
        table_container.controls.append(
            ft.Column(
                [ft.ProgressRing(width=20, height=20), ft.Text("Cargando inventario...")],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        page.update()

        products = api.get_products(search=search_term)
        
        # Si la API devuelve None o hay error de conexión (podemos refinar el api_client después)
        table_container.controls.clear()
        if products is None:
            table_container.controls.append(
                ft.Text("Error de conexión con el servidor. Verifique la API_KEY y URL.", color=ft.Colors.RED, weight="bold")
            )
        else:
            table_container.controls.append(inventory_table(page, products, refresh_callback=refresh_table))
        page.update()

    # --- Lógica de Exportación ---
    async def handle_export(format):
        page.snack_bar = ft.SnackBar(ft.Text(f"Generando reporte {format.upper()}..."))
        page.snack_bar.open = True
        page.update()

        content = api.export_inventory(format=format)
        if content:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            ext = "csv" if format == "csv" else "xlsx"
            filename = f"inventario_{timestamp}.{ext}"
            await page.session.export_picker.save_file(
                file_name=filename,
                allowed_extensions=[ext],
                src_bytes=content
            )
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error al generar el reporte o falta de autorización"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    export_buttons = ft.Row(
        [
            ft.Text("Exportar:", weight="bold", size=14),
            ft.IconButton(icon=ft.Icons.FILE_DOWNLOAD, tooltip="Descargar CSV", on_click=lambda _: page.run_task(handle_export, "csv"), icon_color=ft.Colors.GREEN_700),
            ft.IconButton(icon=ft.Icons.TABLE_CHART, tooltip="Descargar Excel", on_click=lambda _: page.run_task(handle_export, "excel"), icon_color=ft.Colors.BLUE_700),
        ],
        alignment=ft.MainAxisAlignment.END,
    )

    # Componentes del Buscador
    search = search_bar(page, on_search=refresh_table)
    
    # Fila de Título y Refresco
    header_row = ft.Row(
        [
            ft.Text("Inventario – Stock", size=28, weight="bold", color=ft.Colors.BLACK),
            ft.IconButton(
                icon=ft.Icons.REFRESH_ROUNDED, 
                tooltip="Actualizar datos", 
                on_click=lambda _: refresh_table(),
                icon_color=ft.Colors.BLUE_700,
                icon_size=28
            )
        ], 
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # Contenedor del Buscador (más ancho y limpio)
    search_container = ft.Container(
        content=search,
        margin=ft.Margin(0, 0, 0, 10) # Izq, Top, Der, Bottom
    )

    # Fila de Información de Stock y Exportación (encima de la tabla)
    stock_info_row = ft.Row(
        [
            ft.Text("Productos en Existencia", size=18, weight="bold", color=ft.Colors.BLUE_GREY_800),
            export_buttons
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Render inicial de la tabla
    refresh_table()

    return ft.Column(
        [
            header_row,
            search_container,
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            stock_info_row,
            table_container
        ],
        scroll="auto",
        expand=True,
        spacing=15
    )
