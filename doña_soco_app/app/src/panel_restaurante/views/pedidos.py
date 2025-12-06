import flet as ft
from database import obtener_pedidos, obtener_total_pedidos, actualizar_estado_pedido
import math

def pedidos_view(page: ft.Page):
    """
    Vista del panel de administración para gestionar los pedidos con paginación y filtro.
    """
    # --- State Management ---
    rows_per_page = 5
    current_page = 1
    total_pages = 1
    start_date_filter = ft.TextField(label="Fecha Inicio (YYYY-MM-DD)", width=200, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    end_date_filter = ft.TextField(label="Fecha Fin (YYYY-MM-DD)", width=200, label_style=ft.TextStyle(color=ft.Colors.BLACK))

    # --- UI Controls ---
    pedidos_data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Cliente", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Teléfono", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Dirección", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Detalles", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Total", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Fecha", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Estado", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Acciones", color=ft.Colors.BLACK)),
        ],
        rows=[],
    )

    page_status = ft.Text(f"Página {current_page} de {total_pages}", color=ft.Colors.BLACK)
    
    first_page_btn = ft.IconButton(icon=ft.Icons.FIRST_PAGE, on_click=lambda e: go_to_page(1))
    prev_page_btn = ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_LEFT, on_click=lambda e: go_to_page(current_page - 1))
    next_page_btn = ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_RIGHT, on_click=lambda e: go_to_page(current_page + 1))
    last_page_btn = ft.IconButton(icon=ft.Icons.LAST_PAGE, on_click=lambda e: go_to_page(total_pages))

    pagination_controls = ft.Row([ft.Row([first_page_btn, prev_page_btn, page_status, next_page_btn, last_page_btn], alignment=ft.MainAxisAlignment.CENTER)], scroll="auto", alignment=ft.MainAxisAlignment.CENTER)

    # --- Functions ---
    def show_snackbar(text):
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def update_pagination_buttons():
        nonlocal current_page, total_pages
        first_page_btn.disabled = current_page == 1
        prev_page_btn.disabled = current_page == 1
        next_page_btn.disabled = current_page == total_pages
        last_page_btn.disabled = current_page == total_pages
        page_status.value = f"Página {current_page} de {total_pages}"
        page.update()

    def cargar_pedidos():
        nonlocal current_page, total_pages
        
        start_date = start_date_filter.value if start_date_filter.value else None
        end_date = end_date_filter.value if end_date_filter.value else None

        total_items = obtener_total_pedidos(start_date=start_date, end_date=end_date)
        total_pages = math.ceil(total_items / rows_per_page) if total_items > 0 else 1
        if current_page > total_pages:
            current_page = total_pages

        offset = (current_page - 1) * rows_per_page
        pedidos = obtener_pedidos(limit=rows_per_page, offset=offset, start_date=start_date, end_date=end_date)
        
        pedidos_data_table.rows.clear()
        
        if not pedidos:
            pedidos_data_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("No se encontraron pedidos con los filtros aplicados.", color=ft.Colors.BLACK), colspan=9)]))
        else:
            for pedido in pedidos:
                def on_status_change(e, order_id=pedido["id"]):
                    if actualizar_estado_pedido(order_id, e.control.value):
                        show_snackbar(f"Pedido #{order_id} actualizado.")
                        cargar_pedidos()
                    else:
                        show_snackbar(f"Error al actualizar pedido #{order_id}.")

                estado_dropdown = ft.Dropdown(
                    options=[ft.dropdown.Option(estado) for estado in ['Nuevo', 'En preparación', 'Listo para entregar', 'En camino', 'Entregado', 'Cancelado']],
                    value=pedido["estado"],
                    on_change=on_status_change,
                    width=150,
                    text_style=ft.TextStyle(color=ft.Colors.BLACK)
                )

                pedidos_data_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(pedido["id"]), color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["nombre_cliente"], color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["telefono"], color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["direccion"], color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["detalles_productos"] or "N/A", color=ft.Colors.BLACK, size=11)),
                        ft.DataCell(ft.Text(f"${pedido['total']:.2f}", color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["fecha"], color=ft.Colors.BLACK)),
                        ft.DataCell(estado_dropdown),
                        ft.DataCell(ft.Container()),
                    ])
                )
        update_pagination_buttons()
        page.update()

    def go_to_page(page_number):
        nonlocal current_page
        if 1 <= page_number <= total_pages:
            current_page = page_number
            cargar_pedidos()

    def apply_filters(e):
        nonlocal current_page
        current_page = 1
        cargar_pedidos()

    # --- Initial Load ---
    cargar_pedidos()

    # --- Layout ---
    filter_bar = ft.Row([ft.Row([
        start_date_filter,
        end_date_filter,
        ft.ElevatedButton("Filtrar", on_click=apply_filters),
        ft.ElevatedButton("Limpiar", on_click=lambda e: (setattr(start_date_filter, "value", ""), setattr(end_date_filter, "value", ""), apply_filters(e)))
    ], alignment=ft.MainAxisAlignment.START, spacing=10)], scroll="auto")

    return ft.Column(
        [
            ft.Text("Gestión de Pedidos", size=24, weight="bold", color=ft.Colors.BLACK),
            filter_bar,
            pagination_controls,
            ft.Row([pedidos_data_table], scroll="always"), # Table with H-scroll
            pagination_controls,
        ],
        expand=True,
        scroll="auto", # Main V-scroll for the whole view
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=5,
    )
