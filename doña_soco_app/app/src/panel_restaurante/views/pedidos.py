import flet as ft
from database import obtener_pedidos, obtener_total_pedidos, actualizar_estado_pedido
import math

def pedidos_view(page: ft.Page):
    """
    Vista del panel de administración para gestionar los pedidos con paginación y filtro.
    """
    # --- Dialogo de Detalles ---
    def close_details_dialog(e):
        details_dialog.open = False
        page.update()

    details_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Detalles del Pedido"),
        content=ft.Column(), # El contenido se llenará dinámicamente
        actions=[ft.TextButton("Cerrar", on_click=close_details_dialog)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(details_dialog)

    def open_details_dialog(e, pedido):
        detalles_productos_lista = pedido["detalles_productos"].split(" | ") if pedido["detalles_productos"] else []
        
        details_dialog.title = ft.Text(f"Detalles del Pedido #{pedido['id']}")
        details_dialog.content.controls = [
            ft.Text(f"Cliente: {pedido['nombre_cliente']}", weight="bold"),
            ft.Text(f"Teléfono: {pedido['telefono']}"),
            ft.Text(f"Dirección: {pedido['direccion']}"),
            ft.Text(f"Referencias: {pedido['referencias'] or 'N/A'}"),
            ft.Divider(),
            ft.Text("Productos:", weight="bold"),
            ft.Column([ft.Text(f"- {item}") for item in detalles_productos_lista]),
            ft.Divider(),
            ft.Text(f"Total: ${pedido['total']:.2f}", weight="bold", size=16),
            ft.Text(f"Fecha: {pedido['fecha']}"),
            ft.Text(f"Estado Actual: {pedido['estado']}", weight="bold"),
        ]
        details_dialog.open = True
        page.update()

    # --- State Management ---
    rows_per_page = 5
    current_page = 1
    total_pages = 1
    start_date_filter = ft.TextField(label="Fecha Inicio (AAAA-MM-DD)", width=200, label_style=ft.TextStyle(color=ft.Colors.BLACK))
    end_date_filter = ft.TextField(label="Fecha Fin (AAAA-MM-DD)", width=200, label_style=ft.TextStyle(color=ft.Colors.BLACK))

    # --- Confirmation Dialog ---
    def close_dialog(e=None):
        confirmation_dialog.open = False
        page.update()

    confirmation_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Cambio"),
        content=ft.Text("¿Desea cambiar el estado de este pedido?"),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dialog),
            ft.TextButton("Confirmar"), # on_click will be set dynamically
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(confirmation_dialog)


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
                def confirm_and_update(e, order_id, new_status):
                    close_dialog()
                    if actualizar_estado_pedido(order_id, new_status):
                        show_snackbar(f"Pedido #{order_id} actualizado a '{new_status}'.")
                        cargar_pedidos()
                    else:
                        show_snackbar(f"Error al actualizar pedido #{order_id}.")
                        cargar_pedidos() # Recargar para revertir visualmente el dropdown

                def open_confirmation(e, order_id=pedido["id"], old_status=pedido["estado"]):
                    new_status = e.control.value
                    
                    # Restaurar visualmente el dropdown si se cancela
                    def on_cancel(e):
                        e.control.value = old_status
                        close_dialog()
                        cargar_pedidos()

                    confirmation_dialog.content = ft.Text(f"¿Desea cambiar el estado del pedido #{order_id} de '{old_status}' a '{new_status}'?")
                    confirmation_dialog.actions[0].on_click = on_cancel
                    confirmation_dialog.actions[1].on_click = lambda ev: confirm_and_update(ev, order_id, new_status)
                    confirmation_dialog.open = True
                    page.update()

                estado_dropdown = ft.Dropdown(
                    options=[ft.dropdown.Option(estado) for estado in ['Nuevo', 'En preparación', 'Listo para entregar', 'En camino', 'Entregado', 'Cancelado']],
                    value=pedido["estado"],
                    width=150,
                    text_style=ft.TextStyle(color=ft.Colors.BLACK)
                )
                estado_dropdown.on_change = open_confirmation

                pedidos_data_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(pedido["id"]), color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["nombre_cliente"], color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["telefono"], color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["direccion"], color=ft.Colors.BLACK, overflow=ft.TextOverflow.ELLIPSIS, width=150)),
                        ft.DataCell(ft.Text(pedido["detalles_productos"] or "N/A", color=ft.Colors.BLACK, size=11, overflow=ft.TextOverflow.ELLIPSIS, width=200)),
                        ft.DataCell(ft.Text(f"${pedido['total']:.2f}", color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["fecha"], color=ft.Colors.BLACK)),
                        ft.DataCell(estado_dropdown),
                        ft.DataCell(ft.IconButton(icon=ft.Icons.VISIBILITY, on_click=lambda e, p=pedido: open_details_dialog(e, p), tooltip="Ver Detalles")),
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
        ft.Button(content=ft.Text("Filtrar"), on_click=apply_filters),
        ft.Button(content=ft.Text("Limpiar"), on_click=lambda e: (setattr(start_date_filter, "value", ""), setattr(end_date_filter, "value", ""), apply_filters(e)))
    ], alignment=ft.MainAxisAlignment.START, spacing=10)], scroll="auto")

    return ft.Column(
        [
            ft.Text("Gestión de Pedidos", size=24, weight="bold", color=ft.Colors.BLACK),
            filter_bar,
            ft.Row([pedidos_data_table], scroll="always"), # Table with H-scroll
            pagination_controls, # Second instance
        ],
        expand=True,
        scroll="auto", # Main V-scroll for the whole view
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=5,
    )
