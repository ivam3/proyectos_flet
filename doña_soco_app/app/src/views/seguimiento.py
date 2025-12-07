import flet as ft
import sqlite3
import os
from components.notifier import init_pubsub
from database import obtener_pedido_por_codigo

DB_PATH = os.path.join(os.path.dirname(__file__), "../../storage/data/dona_soco.db")

def seguimiento_view(page: ft.Page):
    """Pantalla donde el cliente ve y recibe actualizaciones de un pedido específico."""

    pubsub = init_pubsub(page)

    # --- CAMPOS DE BÚSQUEDA ---
    telefono_guardado = page.client_storage.get("telefono_cliente")
    telefono_field = ft.TextField(
        label="Tu número de teléfono",
        keyboard_type=ft.KeyboardType.PHONE,
        value=telefono_guardado or "",
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )
    codigo_field = ft.TextField(
        label="Código de Seguimiento",
        hint_text="Ej: A4T-G8B",
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    resultado_container = ft.Column(scroll="auto")

    # --- FUNCIÓN PARA ACTUALIZAR PANTALLA ---
    def mostrar_pedido(pedido):
        resultado_container.controls.clear()
        if not pedido:
            resultado_container.controls.append(
                ft.Text("📭 No se encontró ningún pedido con esos datos.", color=ft.Colors.BLACK)
            )
            page.update()
            return

        orden_id, _, _, _, _, _, fecha, estado, _ = pedido

        # Obtener historial del pedido
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT nuevo_estado, fecha
            FROM historial_estados
            WHERE orden_id = ?
            ORDER BY fecha ASC
        """, (orden_id,))
        historial = cursor.fetchall()
        conexion.close()

        # Generar timeline visual
        pasos = [
            ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREY),
                ft.Text(f"{h_estado.title()} — {h_fecha}", size=13, color=ft.Colors.BLACK)
            ]) for h_estado, h_fecha in historial
        ]
        
        color_estado_actual = {
            "Nuevo": ft.Colors.BLUE_GREY,
            "En preparación": ft.Colors.ORANGE,
            "Listo para entregar": ft.Colors.AMBER,
            "En camino": ft.Colors.TEAL_700,
            "Entregado": ft.Colors.GREEN,
            "Cancelado": ft.Colors.RED_400,
        }.get(estado, ft.Colors.GREY)

        resultado_container.controls.append(
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text(f"Pedido #{orden_id}", size=18, weight="bold", color=ft.Colors.BLACK),
                        ft.Text(f"Fecha: {fecha}", color=ft.Colors.BLACK),
                        ft.Text(f"Estado actual: {estado.upper()}", color=color_estado_actual, size=16, weight="bold"),
                        ft.Divider(),
                        ft.Text("Historial de estados:", size=14, weight="bold", color=ft.Colors.BLACK),
                        *pasos
                    ])
                )
            )
        )
        page.update()

    def buscar_pedidos(e):
        tel = telefono_field.value.strip()
        codigo = codigo_field.value.strip().upper()

        if not tel or not codigo:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, ingresa el teléfono y el código de seguimiento."))
            page.snack_bar.open = True
            page.update()
            return

        page.client_storage.set("telefono_cliente", tel)
        
        pedido = obtener_pedido_por_codigo(tel, codigo)
        mostrar_pedido(pedido)

    # --- ESCUCHAR NOTIFICACIONES PUBSUB ---
    def recibir_mensaje(data):
        tel = telefono_field.value.strip()
        codigo = codigo_field.value.strip().upper()
        
        if not tel or not codigo:
            return
        
        # Si la notificación es para el pedido que se está viendo
        if data.get("telefono") == tel and data.get("orden_id") == obtener_pedido_por_codigo(tel, codigo)["id"]:
            sound_path = os.path.join(os.path.dirname(__file__), "../../assets/notify.mp3")
            if os.path.exists(sound_path):
                audio = ft.Audio(src=f"/{sound_path}", autoplay=True)
                page.overlay.append(audio)

            page.snack_bar = ft.SnackBar(ft.Text(f"🔔 Tu pedido #{data['orden_id']} ahora está '{data['nuevo_estado']}'"))
            page.snack_bar.open = True
            buscar_pedidos(None) # Recargar la vista

    pubsub.subscribe(recibir_mensaje)

    return ft.Column([
        ft.Text("📲 Seguimiento de tu pedido", size=24, weight="bold", color=ft.Colors.BLACK),
        ft.Divider(),
        telefono_field,
        codigo_field,
        ft.ElevatedButton("Buscar pedido", on_click=buscar_pedidos),
        ft.Divider(),
        resultado_container
    ], scroll="auto", expand=True)
