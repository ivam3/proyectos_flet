import flet as ft
from database import obtener_pedidos, actualizar_estado_pedido

def pedidos_view(page: ft.Page):
    """
    Vista del panel de administración para gestionar los pedidos.
    """
    pedidos_data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Teléfono")),
            ft.DataColumn(ft.Text("Dirección")),
            ft.DataColumn(ft.Text("Detalles de Productos")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Fecha")),
            ft.DataColumn(ft.Text("Estado")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        expand=True,
    )

    # Posibles estados del pedido
    POSIBLES_ESTADOS = ['Nuevo', 'En preparación', 'Listo para entregar', 'En camino', 'Entregado', 'Cancelado']

    def show_snackbar(text):
        snack = ft.SnackBar(ft.Text(text))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def cargar_pedidos():
        """Carga los pedidos desde la base de datos y actualiza la tabla."""
        pedidos = obtener_pedidos()
        pedidos_data_table.rows.clear()
        
        if not pedidos:
            pedidos_data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("No hay pedidos registrados.")),
                        ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")), ft.DataCell(ft.Text("")),
                    ]
                )
            )
        else:
            for pedido in pedidos:
                # ft.Row for dropdown and button
                def on_status_change(e, order_id=pedido["id"]):
                    nuevo_estado = e.control.value
                    if actualizar_estado_pedido(order_id, nuevo_estado):
                        show_snackbar(f"Pedido {order_id} actualizado a '{nuevo_estado}'")
                        cargar_pedidos() # Recargar para reflejar el cambio
                    else:
                        show_snackbar(f"Error al actualizar pedido {order_id}")
                
                estado_dropdown = ft.Dropdown(
                    options=[ft.dropdown.Option(estado) for estado in POSIBLES_ESTADOS],
                    value=pedido["estado"],
                    on_change=on_status_change,
                    width=150,
                )

                pedidos_data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(pedido["id"]))),
                            ft.DataCell(ft.Text(pedido["nombre_cliente"])),
                            ft.DataCell(ft.Text(pedido["telefono"])),
                            ft.DataCell(ft.Text(pedido["direccion"])),
                            ft.DataCell(ft.Text(pedido["detalles_productos"] or "N/A")),
                            ft.DataCell(ft.Text(f"${pedido['total']:.2f}")),
                            ft.DataCell(ft.Text(pedido["fecha"])),
                            ft.DataCell(estado_dropdown),
                            ft.DataCell(ft.Container()), # Placeholder for more actions if needed
                        ]
                    )
                )
        page.update()

    # Carga inicial de pedidos
    cargar_pedidos()

    return ft.Column(
        [
            ft.Text("Gestión de Pedidos", size=30, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton("Actualizar Pedidos", on_click=lambda e: cargar_pedidos()),
            ]),
            ft.Container(
                content=ft.Column([pedidos_data_table], scroll="auto", expand=True),
                expand=True,
                padding=10,
            )
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )