import flet as ft
import sqlite3
import os
from components.notifier import init_pubsub
from ..config import APP_NAME

DB_PATH = os.path.join(os.path.dirname(__file__), "../../../storage/data/dona_soco.db")

ESTADOS = ["pendiente", "en preparación", "en camino", "entregado"]


def obtener_pedidos():
    """Obtiene todos los pedidos registrados."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, nombre_cliente, telefono, direccion, total, fecha, estado 
        FROM ordenes 
        ORDER BY fecha DESC
    """)
    pedidos = cursor.fetchall()
    conexion.close()
    return pedidos


def obtener_detalle(orden_id):
    """Obtiene los productos de una orden específica."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT producto, cantidad, precio_unitario 
        FROM orden_detalle 
        WHERE orden_id = ?
    """, (orden_id,))
    detalles = cursor.fetchall()
    conexion.close()
    return detalles


def actualizar_estado(orden_id, nuevo_estado):
    """Actualiza el estado de un pedido."""
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("UPDATE ordenes SET estado = ? WHERE id = ?", (nuevo_estado, orden_id))
    conexion.commit()
    conexion.close()


def crear_panel_pedidos(page: ft.Page):
    """Pantalla del panel administrativo de pedidos."""

    pedidos_data = obtener_pedidos()

    pedidos_list = ft.ListView(expand=True, spacing=10)

    def mostrar_detalle(e, orden_id):
        detalles = obtener_detalle(orden_id)
        contenido = "\n".join([f"🍽 {p[0]} x{p[1]} - ${p[2]:.2f}" for p in detalles])
        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalle del pedido #{orden_id}"),
            content=ft.Text(contenido if contenido else "Sin detalles registrados."),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo(dlg, page))],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def cerrar_dialogo(dialog, page):
        dialog.open = False
        page.update()

    def cambiar_estado(e, orden_id, estado_dropdown):
        nuevo_estado = estado_dropdown.value
        actualizar_estado(orden_id, nuevo_estado)
        page.snack_bar = ft.SnackBar(ft.Text(f"Estado del pedido #{orden_id} actualizado a '{nuevo_estado}' ✅"))
        page.snack_bar.open = True
        page.update()

        # Guardar el cambio en historial
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO historial_estados (orden_id, nuevo_estado)
            VALUES (?, ?)
        """, (orden_id, nuevo_estado))
        conexion.commit()
        
        # Obtener teléfono del pedido para notificar al cliente
        cursor.execute("SELECT telefono FROM ordenes WHERE id = ?", (orden_id,))
        telefono = cursor.fetchone()[0]
        conexion.close()
        
        # Publicar notificación a todos los clientes
        from components.notifier import init_pubsub
        pubsub = init_pubsub(page)
        pubsub.send_all({
            "telefono": telefono,
            "orden_id": orden_id,
            "nuevo_estado": nuevo_estado
        })

        page.snack_bar = ft.SnackBar(ft.Text(f"Estado del pedido #{orden_id} actualizado a '{nuevo_estado}' ✅"))
        page.snack_bar.open = True
        page.update()

# Generar lista de pedidos
for p in pedidos_data:
    orden_id, nombre, tel, dir, total, fecha, estado = p
    estado_dropdown = ft.Dropdown(
        value=estado,
        options=[ft.dropdown.Option(op) for op in ESTADOS],
        on_change=lambda e, oid=orden_id, s=None: cambiar_estado(e, oid, e.control),
        width=180
    )

    pedidos_list.controls.append(
        ft.Card(
            content=ft.Container(
                padding=10,
                content=ft.Column(
                    [
                        ft.Text(f"Pedido #{orden_id} - {nombre}", size=18, weight="bold"),
                        ft.Text(f"📅 {fecha}  |  ☎️ {tel}"),
                        ft.Text(f"🏠 {dir}"),
                        ft.Text(f"💰 Total: ${total:.2f}"),
                        ft.Row(
                            [
                                estado_dropdown,
                                ft.Button("Ver detalle", on_click=lambda e, oid=orden_id: mostrar_detalle(e, oid)),
                            ],
                            spacing=10
                        )
                    ]
                )
            )
        )
    )

return ft.View(
    "/admin/pedidos",
    [
        ft.AppBar(title=ft.Text(f"Panel de Pedidos - {APP_NAME}"), bgcolor=ft.Colors.ORANGE),
        ft.Container(
            padding=20,
            content=pedidos_list
        )
    ]
)

