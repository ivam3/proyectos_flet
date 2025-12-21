import flet as ft
from database import obtener_pedidos, obtener_total_pedidos, actualizar_estado_pedido, actualizar_pago_pedido
import math
import csv
import datetime
import io

def pedidos_view(page: ft.Page, export_file_picker: ft.FilePicker):
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
        
        metodo = pedido["metodo_pago"] or "N/A"
        paga_con = pedido["paga_con"] or 0
        cambio = paga_con - pedido["total"] if metodo == "efectivo" and paga_con else 0
        
        pago_info = [ft.Text(f"Método de Pago: {metodo.capitalize()}", weight="bold")]
        if metodo == "efectivo":
            pago_info.append(ft.Text(f"Paga con: ${paga_con:.2f}"))
            pago_info.append(ft.Text(f"Cambio: ${cambio:.2f}", color=ft.Colors.GREEN if cambio >= 0 else ft.Colors.RED))

        details_dialog.title = ft.Text(f"Pedido #{pedido['id']}")
        details_dialog.content = ft.Container(
            content=ft.Column([
                ft.Text(f"Código Seguimiento: {pedido['codigo_seguimiento']}", weight="bold", size=16, color=ft.Colors.BLUE_GREY_700),
                ft.Divider(),
                ft.Text(f"Cliente: {pedido['nombre_cliente']}", weight="bold"),
                ft.Text(f"Teléfono: {pedido['telefono']}"),
                ft.Text(f"Dirección: {pedido['direccion']}"),
                ft.Text(f"Referencias: {pedido['referencias'] or 'N/A'}"),
                ft.Divider(),
                ft.Text("Productos:", weight="bold"),
                ft.Column([ft.Text(f"- {item}") for item in detalles_productos_lista]),
                ft.Divider(),
                ft.Column(pago_info),
                ft.Divider(),
                ft.Text(f"Total: ${pedido['total']:.2f}", weight="bold", size=16),
                ft.Text(f"Fecha: {pedido['fecha']}"),
                ft.Text(f"Estado Actual: {pedido['estado']}", weight="bold"),
                ft.Text(f"Motivo Cancelación: {pedido['motivo_cancelacion']}", color=ft.Colors.RED_700, weight="bold", visible=(pedido['estado'] == "Cancelado" and bool(pedido['motivo_cancelacion']))),
            ], scroll="auto"),
            height=400, # Altura fija para evitar desbordamiento
            width=350,
        )
        details_dialog.open = True
        page.update()

    # --- State Management ---
    rows_per_page = 12 
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
            ft.DataColumn(ft.Text("Código", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Cliente", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Pago", color=ft.Colors.BLACK)), 
            ft.DataColumn(ft.Text("Denominación", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Dirección", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Total", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Estado", color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Acciones", color=ft.Colors.BLACK)),
        ],
        rows=[],
        heading_row_color=ft.Colors.ORANGE_50,
        data_row_min_height=50,
        column_spacing=20,
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

    async def exportar_csv(e):
        try:
            start_date = start_date_filter.value if start_date_filter.value else None
            end_date = end_date_filter.value if end_date_filter.value else None
            
            all_pedidos = obtener_pedidos(limit=100000, offset=0, start_date=start_date, end_date=end_date)
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Código", "Cliente", "Teléfono", "Dirección", "Referencia", "Total", "Fecha", "Estado", "Método Pago", "Paga Con", "Detalles"])
            for p in all_pedidos:
                writer.writerow([
                    p["id"], p["codigo_seguimiento"], p["nombre_cliente"], p["telefono"], 
                    p["direccion"], p["referencias"], p["total"], p["fecha"], p["estado"],
                    p["metodo_pago"], p["paga_con"], p["detalles_productos"]
                ])
            
            csv_bytes = output.getvalue().encode('utf-8')
            output.close()

            filename = f"pedidos_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Forzamos visibilidad False antes de llamar
            export_file_picker.visible = False
            await export_file_picker.save_file(file_name=filename, allowed_extensions=["csv"], src_bytes=csv_bytes)
            show_snackbar(f"Exportación iniciada.")

        except Exception as ex:
            show_snackbar(f"Error al exportar: {ex}")

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
        
        def confirm_and_update(e, order_id, new_status, motivo=None):
            close_dialog()
            if actualizar_estado_pedido(order_id, new_status, motivo):
                show_snackbar(f"Pedido #{order_id} actualizado a '{new_status}'.")
                cargar_pedidos()
            else:
                show_snackbar(f"Error al actualizar pedido #{order_id}.")
                cargar_pedidos() 

        # Dialog for cancellation reason
        motivo_field = ft.TextField(label="Motivo de cancelación", multiline=True)
        cancellation_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cancelar Pedido"),
            content=ft.Column([
                ft.Text("Por favor, ingrese el motivo de la cancelación:"),
                motivo_field
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(cancellation_dialog, "open", False) or page.update()),
                ft.TextButton("Confirmar Cancelación", style=ft.ButtonStyle(color=ft.Colors.RED)), # on_click set dynamically
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(cancellation_dialog)

        def open_confirmation(e, order_id, old_status):
            new_status = e.control.value
            if new_status == old_status:
                return

            def on_cancel(ev):
                close_dialog()
                cargar_pedidos()

            if new_status == "Cancelado":
                motivo_field.value = ""
                
                def on_confirm_cancel(ev):
                    if not motivo_field.value.strip():
                        motivo_field.error_text = "El motivo es obligatorio"
                        page.update()
                        return
                    cancellation_dialog.open = False
                    page.update() # Update page to close dialog visually
                    confirm_and_update(ev, order_id, new_status, motivo_field.value.strip())

                cancellation_dialog.actions[1].on_click = on_confirm_cancel
                cancellation_dialog.open = True
                page.update()
            else:
                confirmation_dialog.content = ft.Text(f"¿Desea cambiar el estado del pedido #{order_id} de '{old_status}' a '{new_status}'?")
                confirmation_dialog.actions[0].on_click = on_cancel
                confirmation_dialog.actions[1].on_click = lambda ev: confirm_and_update(ev, order_id, new_status)
                confirmation_dialog.open = True
                page.update()

        if not pedidos:
            pedidos_data_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("No se encontraron pedidos.", color=ft.Colors.BLACK), colspan=9)]))
        else:
            for pedido in pedidos:
                order_id = pedido["id"]
                current_status = pedido["estado"]
                
                estado_dropdown = ft.Dropdown(
                    options=[ft.dropdown.Option(estado) for estado in ['Nuevo', 'En preparación', 'Listo para entregar', 'En camino', 'Entregado', 'Cancelado']],
                    value=current_status,
                    width=150,
                    text_style=ft.TextStyle(color=ft.Colors.BLACK),
                    on_select=lambda e, oid=order_id, ost=current_status: open_confirmation(e, oid, ost)
                )

                metodo_pago = pedido["metodo_pago"] or "N/A"
                paga_con_val = pedido["paga_con"] if pedido["paga_con"] else 0.0
                paga_con_display = f"${paga_con_val:.2f}" if metodo_pago == "efectivo" else "N/A"

                pedidos_data_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(pedido["id"]), color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(str(pedido["codigo_seguimiento"]), weight="bold", color=ft.Colors.BLUE_GREY_700)),
                        ft.DataCell(ft.Text(pedido["nombre_cliente"], color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(metodo_pago.capitalize(), color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(paga_con_display, color=ft.Colors.BLACK)),
                        ft.DataCell(ft.Text(pedido["direccion"], color=ft.Colors.BLACK, overflow=ft.TextOverflow.ELLIPSIS, width=150)),
                        ft.DataCell(ft.Text(f"${pedido['total']:.2f}", color=ft.Colors.BLACK)),
                        ft.DataCell(estado_dropdown),
                        ft.DataCell(ft.IconButton(icon=ft.Icons.VISIBILITY, on_click=lambda e, p=pedido: open_details_dialog(e, p))),
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

    cargar_pedidos()

    filter_bar = ft.Row([ft.Row([
        start_date_filter,
        end_date_filter,
        ft.Button(content=ft.Text("Filtrar"), on_click=apply_filters),
        ft.Button(content=ft.Text("Limpiar"), on_click=lambda e: (setattr(start_date_filter, "value", ""), setattr(end_date_filter, "value", ""), apply_filters(e))),
        ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Actualizar Tabla", on_click=lambda _: cargar_pedidos()),
        ft.VerticalDivider(),
        ft.Button(content=ft.Text("Exportar CSV"), icon=ft.Icons.DOWNLOAD, on_click=exportar_csv),
        ft.Button(content=ft.Text("Exportar XLSM"), icon=ft.Icons.TABLE_VIEW, on_click=exportar_csv)
    ], alignment=ft.MainAxisAlignment.START, spacing=10)], scroll="auto")

    return ft.Column(
        [
            ft.Text("Gestión de Pedidos", size=24, weight="bold", color=ft.Colors.BLACK),
            filter_bar,
            ft.Row([pedidos_data_table], scroll="always", expand=True),
            pagination_controls,
        ],
        expand=True,
        scroll="auto",
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=5,
    )
