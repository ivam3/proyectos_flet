import flet as ft
from database import obtener_pedidos, obtener_total_pedidos, actualizar_estado_pedido, actualizar_pago_pedido, obtener_datos_exportacion
import math
import csv
import datetime
import io
import os
from fpdf import FPDF

def pedidos_view(page: ft.Page, export_file_picker: ft.FilePicker):
    """
    Vista del panel de administración para gestionar los pedidos con paginación y filtro.
    """
    # --- State Management ---
    rows_per_page = 12 
    current_page = 1
    total_pages = 1
    
    # Campo de búsqueda (estilo unificado con menú usuario)
    search_filter = ft.TextField(
        hint_text="Buscar por Cliente o Código",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=20, height=40,
        text_size=14, content_padding=10, filled=True,
    )

    # --- Lógica de Mensajería Post-Guardado ---
    pending_save_content = {"data": None}
    
    # Crear un FilePicker local para evitar conflictos con el global
    file_picker = ft.FilePicker()
    # page.overlay.append(file_picker) # REMOVED: Causes Red Stripe bug on Android

    def on_file_picker_result(e):
        if e.path:
            if pending_save_content["data"]:
                try:
                    with open(e.path, "wb") as f:
                        f.write(pending_save_content["data"])
                    page.snack_bar = ft.SnackBar(ft.Text(f"Archivo guardado correctamente en: {os.path.basename(e.path)}"), bgcolor=ft.Colors.GREEN)
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar: {ex}"), bgcolor=ft.Colors.RED)
                finally:
                    pending_save_content["data"] = None
            else:
                 page.snack_bar = ft.SnackBar(ft.Text(f"Seleccionado: {e.path}"))
            
            page.snack_bar.open = True
            page.update()

    file_picker.on_result = on_file_picker_result

    # --- Lógica de Exportación (CSV/Excel) ---
    async def iniciar_exportacion(extension="csv"):
        # Mensaje de feedback inmediato
        page.snack_bar = ft.SnackBar(ft.Text(f"Generando reporte {extension.upper()}..."))
        page.snack_bar.open = True
        page.update()

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "csv" if extension == "csv" else "xlsm" 
            
            # 1. Generar datos desde la DB
            search_term = search_filter.value.strip() if search_filter.value else None
            datos = obtener_datos_exportacion(search_term=search_term)
            
            headers = [
                "Orden ID", "Código", "Fecha", "Cliente", "Teléfono", "Dirección", "Referencias", 
                "Estado", "Método Pago", "Paga Con", "Total Orden", "Motivo Cancelación",
                "Producto", "Cantidad", "Precio Unitario", "Subtotal Producto"
            ]
            
            # 2. Escribir a memoria
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            for row in datos:
                writer.writerow(list(row))
            
            # 3. Obtener bytes
            csv_content = output.getvalue()
            src_bytes = csv_content.encode('utf-8')
            output.close()
            
            pending_save_content["data"] = src_bytes

            # 4. Abrir diálogo de guardado
            await file_picker.save_file(
                dialog_title=f"Guardar reporte ({ext.upper()})",
                file_name=f"reporte_pedidos_{timestamp}.{ext}",
                allowed_extensions=[ext],
                src_bytes=src_bytes
            )

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    # --- Lógica de PDF Individual ---
    async def generar_y_guardar_pdf(pedido):
        page.snack_bar = ft.SnackBar(ft.Text("Generando PDF..."))
        page.snack_bar.open = True
        page.update()

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=f"Detalle del Pedido #{pedido['id']}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, txt=f"Fecha: {pedido['fecha']}", ln=True)
            pdf.cell(0, 10, txt=f"Código: {pedido['codigo_seguimiento']}", ln=True)
            pdf.cell(0, 10, txt=f"Estado: {pedido['estado']}", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="Datos del Cliente", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, txt=f"Nombre: {pedido['nombre_cliente']}", ln=True)
            pdf.cell(0, 8, txt=f"Teléfono: {pedido['telefono']}", ln=True)
            pdf.multi_cell(0, 8, txt=f"Dirección: {pedido['direccion']}")
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="Productos", ln=True)
            pdf.set_font("Arial", size=12)
            
            detalles_lista = pedido["detalles_productos"].split(" | ") if pedido["detalles_productos"] else []
            for item in detalles_lista:
                safe_item = item.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 8, txt=f"- {safe_item}")
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt=f"Total: ${pedido['total']:.2f}", ln=True, align='R')

            # Obtener bytes del PDF
            pdf_str = pdf.output(dest='S')
            pdf_bytes = pdf_str.encode('latin-1')

            pending_save_content["data"] = pdf_bytes

            await file_picker.save_file(
                dialog_title=f"Guardar PDF Pedido #{pedido['id']}",
                file_name=f"pedido_{pedido['id']}.pdf",
                allowed_extensions=["pdf"],
                src_bytes=pdf_bytes
            )
            
        except Exception as ex:
             page.snack_bar = ft.SnackBar(ft.Text(f"Error PDF: {ex}"), bgcolor=ft.Colors.RED)
             page.snack_bar.open = True
             page.update()

    def create_pdf_handler(pedido):
        async def handler(e):
            await generar_y_guardar_pdf(pedido)
        return handler

    async def export_csv_click(e):
        await iniciar_exportacion("csv")

    async def export_xlsm_click(e):
        await iniciar_exportacion("xlsm")

    # --- Data Table Definition ---
    pedidos_data_table = ft.DataTable(
        heading_row_color=ft.Colors.ORANGE_100,
        heading_row_height=60,
        columns=[
            ft.DataColumn(ft.Text("ID", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Código", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Cliente", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Fecha", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Total", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Pago", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Estado", weight="bold", color=ft.Colors.BLUE_GREY_900)),
            ft.DataColumn(ft.Text("Acciones", weight="bold", color=ft.Colors.BLUE_GREY_900)),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.GREY_300),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
    )

    # --- Dialogo de Detalles ---
    def close_details_dialog(e):
        details_dialog.open = False
        page.update()

    details_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Detalles del Pedido"),
        content=ft.Column(), 
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
            height=400, width=350,
        )
        details_dialog.open = True
        page.update()

    # --- Confirmation/Status Dialog ---
    def close_confirmation_dialog(e=None):
        confirmation_dialog.open = False
        page.update()

    def confirm_status_change(e, pedido_id, new_status, motivo=None):
        actualizar_estado_pedido(pedido_id, new_status, motivo)
        close_confirmation_dialog()
        cargar_pedidos()
        page.snack_bar = ft.SnackBar(ft.Text(f"Estado actualizado a {new_status}"))
        page.snack_bar.open = True
        page.update()

    confirmation_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Cambiar Estado"),
        content=ft.Container(),
        actions=[],
    )
    page.overlay.append(confirmation_dialog)

    def open_status_dialog(e, pedido):
        def set_status(status):
            return lambda e: confirm_status_change(e, pedido['id'], status)

        def show_cancel_reason(e):
            reason_field = ft.TextField(label="Motivo de cancelación", multiline=True)
            
            def confirm_cancel(e):
                if not reason_field.value:
                    reason_field.error_text = "Ingrese un motivo"
                    reason_field.update()
                    return
                confirm_status_change(e, pedido['id'], "Cancelado", reason_field.value)

            confirmation_dialog.title = ft.Text("Cancelar Pedido")
            confirmation_dialog.content = ft.Column([
                ft.Text(f"Ingrese el motivo de cancelación para el pedido #{pedido['id']}:"),
                reason_field
            ], height=150)
            confirmation_dialog.actions = [
                ft.TextButton("Volver", on_click=lambda e: open_status_dialog(e, pedido)),
                ft.FilledButton(
                    "Confirmar Cancelación", 
                    on_click=confirm_cancel, 
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                ),
            ]
            confirmation_dialog.update()

        confirmation_dialog.title = ft.Text(f"Cambiar estado pedido #{pedido['id']}")
        confirmation_dialog.content = ft.Column([
            ft.FilledButton("Pendiente", on_click=set_status("Pendiente"), width=200, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)),
            ft.FilledButton("Preparando", on_click=set_status("Preparando"), width=200, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)),
            ft.FilledButton("En Camino", on_click=set_status("En Camino"), width=200, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)),
            ft.FilledButton("Entregado", on_click=set_status("Entregado"), width=200, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)),
            ft.FilledButton("Cancelado", on_click=show_cancel_reason, width=200, style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)),
        ], height=300, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        confirmation_dialog.actions = [ft.TextButton("Cerrar", on_click=close_confirmation_dialog)]
        confirmation_dialog.open = True
        page.update()

    # --- Pagination Controls ---
    txt_page_info = ft.Text("Página 1 de 1")
    
    def change_page(delta):
        nonlocal current_page
        new_page = current_page + delta
        if 1 <= new_page <= total_pages:
            current_page = new_page
            cargar_pedidos()

    btn_prev = ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: change_page(-1))
    btn_next = ft.IconButton(icon=ft.Icons.ARROW_FORWARD, on_click=lambda e: change_page(1))
    
    pagination_controls = ft.Row(
        [btn_prev, txt_page_info, btn_next],
        alignment=ft.MainAxisAlignment.CENTER
    )

    # --- Cargar Pedidos ---
    def cargar_pedidos():
        nonlocal current_page, total_pages
        search_term = search_filter.value.strip() if search_filter.value else None

        total_items = obtener_total_pedidos(search_term=search_term)
        total_pages = math.ceil(total_items / rows_per_page) if total_items > 0 else 1
        if current_page > total_pages:
            current_page = max(1, total_pages)
        if current_page < 1: current_page = 1

        offset = (current_page - 1) * rows_per_page
        pedidos = obtener_pedidos(limit=rows_per_page, offset=offset, search_term=search_term)
        
        pedidos_data_table.rows.clear()
        
        for p in pedidos:
            pedidos_data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(p['id']))),
                        ft.DataCell(ft.Text(p['codigo_seguimiento'])),
                        ft.DataCell(ft.Text(p['nombre_cliente'])),
                        ft.DataCell(ft.Text(str(p['fecha']))),
                        ft.DataCell(ft.Text(f"${p['total']:.2f}")),
                        ft.DataCell(ft.Text(str(p['metodo_pago']).capitalize())),
                        ft.DataCell(ft.Text(p['estado'])),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.VISIBILITY, tooltip="Ver Detalles", on_click=lambda e, p=p: open_details_dialog(e, p)),
                            ft.IconButton(
                                ft.Icons.EDIT, 
                                tooltip="Cambiar Estado", 
                                on_click=lambda e, p=p: open_status_dialog(e, p),
                                disabled=(p['estado'] == "Cancelado")
                            ),
                            ft.IconButton(
                                ft.Icons.PICTURE_AS_PDF,
                                tooltip="Descargar PDF",
                                icon_color=ft.Colors.RED_700,
                                on_click=create_pdf_handler(p)
                            )
                        ])),
                    ]
                )
            )
        
        txt_page_info.value = f"Página {current_page} de {total_pages}"
        btn_prev.disabled = current_page <= 1
        btn_next.disabled = current_page >= total_pages
        page.update()

    def apply_filters(e):
        nonlocal current_page
        current_page = 1
        cargar_pedidos()

    cargar_pedidos()

    filter_bar = ft.Container(
        content=ft.Column([
            search_filter, 
            ft.Row([
                ft.FilledButton(
                    content=ft.Text("Filtrar"), 
                    on_click=apply_filters,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
                ),
                ft.FilledButton(
                    content=ft.Text("Limpiar"), 
                    on_click=lambda e: (setattr(search_filter, "value", ""), apply_filters(e)),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                ),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: cargar_pedidos()),
            ], scroll="auto", spacing=10),
            ft.Row([
                ft.FilledButton(content=ft.Text("CSV"), icon=ft.Icons.DOWNLOAD, on_click=export_csv_click, expand=True, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)),
                ft.FilledButton(content=ft.Text("XLSM"), icon=ft.Icons.TABLE_VIEW, on_click=export_xlsm_click, expand=True, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE))
            ], spacing=10)
        ], spacing=10),
        padding=10
    )

    content_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Gestión de pedidos", size=20, weight="bold", color=ft.Colors.BLUE_GREY_900),
                filter_bar,
                ft.Row([pedidos_data_table], scroll="always", expand=True),
                pagination_controls,
            ],
            spacing=5,
        ),
        padding=20,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=15,
        expand=True,
    )

    return ft.Column([content_container, ft.Container(content=file_picker, visible=False)], expand=True, scroll="auto")
