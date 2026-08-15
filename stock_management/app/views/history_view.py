import flet as ft
from datetime import datetime

def history_view(page: ft.Page):
    api = page.session.api
    
    # Contenedor para la tabla (Homologado con inventory_view)
    history_container = ft.Column(
        width=float("inf"),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Buscador con ancho fijo para evitar colapsos en Rows con wrap
    search_input = ft.TextField(
        label="Buscar venta, modelo o SKU...", 
        width=300,
        on_submit=lambda _: refresh_history()
    )

    def show_error(msg):
        dlg = ft.AlertDialog(
            title=ft.Text("Error de Datos", color=ft.Colors.RED),
            content=ft.Text(msg),
            actions=[ft.TextButton("Entendido", on_click=lambda _: [setattr(dlg, "open", False), page.update()])]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def on_cancel_sale(movement):
        reason_input = ft.TextField(label="Motivo de cancelación (Obligatorio)", multiline=True)
        waste_chk = ft.Checkbox(label="Marcar como MERMA (No vuelve al stock)", value=False)

        def do_cancel(e):
            if not reason_input.value.strip():
                reason_input.error_text = "El motivo es obligatorio"
                reason_input.update()
                return
            
            if api.cancel_movement(movement['id'], reason_input.value, waste_chk.value):
                page.snack_bar = ft.SnackBar(ft.Text("Venta cancelada exitosamente"), bgcolor=ft.Colors.ORANGE_700)
                dlg.open = False
                refresh_history()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Error al cancelar"), bgcolor=ft.Colors.RED)
            
            page.snack_bar.open = True
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Cancelar Venta #{movement.get('sales_id', movement['id'])}"),
            content=ft.Column([
                ft.Text(f"Producto: {movement['product_name']}"),
                reason_input,
                waste_chk
            ], tight=True, width=400),
            actions=[
                ft.TextButton("Volver", on_click=lambda _: [setattr(dlg, "open", False), page.update()]),
                ft.Button("Confirmar Cancelación", on_click=do_cancel, bgcolor=ft.Colors.RED, color="white")
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def on_finalize_sale(movement):
        def do_finalize(e):
            if api.update_movement_status(movement['id'], "COMPLETED"):
                page.snack_bar = ft.SnackBar(ft.Text("Venta finalizada con éxito"), bgcolor=ft.Colors.GREEN)
                dlg.open = False
                refresh_history()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Error al finalizar"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Venta Final"),
            content=ft.Text(f"¿Deseas marcar la pre-venta #{movement.get('sales_id')} como COMPLETADA?"),
            actions=[
                ft.TextButton("Volver", on_click=lambda _: [setattr(dlg, "open", False), page.update()]),
                ft.Button("Finalizar Venta", on_click=do_finalize, bgcolor=ft.Colors.GREEN, color="white")
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def refresh_history(e=None):
        history_container.controls.clear()
        history_container.controls.append(
            ft.Row([ft.ProgressRing(width=30, height=30), ft.Text(" Cargando historial...")], alignment=ft.MainAxisAlignment.CENTER)
        )
        page.update()

        try:
            all_movements = api.get_movements()
            if all_movements is None:
                history_container.controls.clear()
                history_container.controls.append(
                    ft.Text("Error de autorización o conexión con el servidor.", color=ft.Colors.RED, weight="bold")
                )
                page.update()
                return

            search_term = search_input.value.lower()
            
            movements = []
            for m in all_movements:
                match = (
                    not search_term or 
                    search_term in (m.get('product_name') or "").lower() or 
                    search_term in (m.get('sku') or "").lower() or 
                    search_term in (m.get('sales_id') or "").lower()
                )
                if match: movements.append(m)

            rows = []
            for m in movements:
                fecha_dt = m['created_at'].replace("T", " ")[:16]
                status = m.get('status', 'COMPLETED')
                
                # Definición de Etiquetas y Colores de Estado
                if status == "CANCELLED":
                    status_color = ft.Colors.RED_700
                    status_label = "Cancelado"
                elif status == "PRE-SALE":
                    status_color = ft.Colors.ORANGE_800
                    status_label = "Pre-venta"
                elif m['movement_type'] == "IN":
                    status_color = ft.Colors.BLUE_700
                    status_label = "Entrada"
                else:
                    status_color = ft.Colors.GREEN_700
                    status_label = "Venta"

                actions = ft.Row(spacing=0)
                
                # Acción: Finalizar Pre-venta
                if status == "PRE-SALE":
                    actions.controls.append(
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            tooltip="Finalizar Venta",
                            icon_color=ft.Colors.GREEN,
                            on_click=lambda e, mov=m: on_finalize_sale(mov)
                        )
                    )

                # Acción: Cancelar
                if status != "CANCELLED" and m['movement_type'] == "OUT":
                    actions.controls.append(
                        ft.IconButton(
                            icon=ft.Icons.CANCEL_OUTLINED,
                            tooltip="Cancelar Operación",
                            icon_color=ft.Colors.RED,
                            on_click=lambda e, mov=m: on_cancel_sale(mov)
                        )
                    )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(fecha_dt, size=11)),
                            ft.DataCell(ft.Text(m.get('sales_id') or "-", weight="bold")),
                            ft.DataCell(ft.Column([
                                ft.Text(m['product_name'], weight="bold", size=13),
                                ft.Text(f"SKU: {m.get('sku', '-')}", size=10, color=ft.Colors.GREY_700)
                            ], tight=True)),
                            ft.DataCell(ft.Text(f"{m.get('color', 'N/A')}\nTalla {m['size_label']}", size=11)),
                            ft.DataCell(ft.Text(status_label, color=status_color, weight="bold", size=11)),
                            ft.DataCell(ft.Text(m.get('distribution_channel') or "-", size=11)),
                            ft.DataCell(ft.Text(str(m['quantity']))),
                            ft.DataCell(ft.Text(f"${m.get('final_price', 0):.2f}" if m.get('final_price') else "-")),
                            ft.DataCell(actions),
                        ]
                    )
                )

            history_container.controls.clear()
            if not rows:
                history_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=50, color=ft.Colors.GREY_400),
                                ft.Text("Historial vacío", size=18, color=ft.Colors.GREY_600, weight="bold"),
                                ft.Text("Las ventas y movimientos aparecerán aquí", size=14, color=ft.Colors.GREY_500),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=50
                    )
                )
            else:
                table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Fecha")),
                        ft.DataColumn(ft.Text("ID Venta")),
                        ft.DataColumn(ft.Text("Producto")),
                        ft.DataColumn(ft.Text("Var")),
                        ft.DataColumn(ft.Text("Tipo")),
                        ft.DataColumn(ft.Text("Canal")),
                        ft.DataColumn(ft.Text("Cant")),
                        ft.DataColumn(ft.Text("Total")),
                        ft.DataColumn(ft.Text("Acción")),
                    ],
                    rows=rows,
                    heading_row_color=ft.Colors.GREY_100,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    column_spacing=15
                )
                history_container.controls.append(ft.Row([table], scroll=ft.ScrollMode.ALWAYS))
            
        except Exception as ex:
            history_container.controls.clear()
            history_container.controls.append(ft.Text(f"Error al cargar: {ex}", color=ft.Colors.RED))
            show_error(f"No se pudo obtener el historial. Detalle: {ex}")
        
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
            page.snack_bar = ft.SnackBar(ft.Text("Error al generar el reporte"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    export_buttons = ft.Row(
        [
            ft.Text("Exportar:", weight="bold"),
            ft.TextButton("CSV", icon=ft.Icons.FILE_DOWNLOAD, on_click=lambda _: page.run_task(handle_export, "csv")),
            ft.TextButton("Excel", icon=ft.Icons.TABLE_CHART, on_click=lambda _: page.run_task(handle_export, "excel")),
        ],
        wrap=True
    )

    # Render inicial
    refresh_history()

    return ft.Column(
        [
            ft.Row([
                ft.Text("Historial de Movimientos", size=26, weight="bold"),
                ft.IconButton(ft.Icons.REFRESH, on_click=refresh_history)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ft.Row([search_input, export_buttons], wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(),
            history_container 
        ],
        scroll="auto", # El scroll lo maneja la columna principal, igual que en inventario
        expand=True,
        spacing=10
    )
