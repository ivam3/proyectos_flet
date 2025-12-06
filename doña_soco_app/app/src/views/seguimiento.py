import flet as ft
import sqlite3
import os
from components.notifier import init_pubsub

DB_PATH = os.path.join(os.path.dirname(__file__), "../../storage/data/dona_soco.db")

def seguimiento_view(page: ft.Page):
    """Pantalla donde el cliente ve y recibe actualizaciones del pedido en tiempo real."""

    pubsub = init_pubsub(page)

    # Recuperar número de teléfono guardado
    telefono_guardado = page.client_storage.get("telefono_cliente")
    telefono_field = ft.TextField(
        label="Tu número de teléfono",
        keyboard_type=ft.KeyboardType.PHONE,
        value=telefono_guardado or "",
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    resultado_text = ft.Text("", size=16, color=ft.Colors.BLACK)
    pedidos_list = ft.Column(scroll="auto")

    # --- FUNCIÓN PARA ACTUALIZAR PANTALLA ---
    def actualizar_pedidos(tel):
        pedidos_list.controls.clear()
        if not tel:
            resultado_text.value = "⚠️ Ingresa un número de teléfono."
            page.update()
            return

        # Guardar de nuevo el número (por si se modificó)
        page.client_storage.set("telefono_cliente", tel)
        
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, fecha, total, estado
            FROM ordenes
            WHERE telefono = ?
            ORDER BY fecha DESC
        """, (tel,))
        pedidos = cursor.fetchall()
        conexion.close()

        if not pedidos:
            resultado_text.value = "📭 No hay pedidos asociados a este número."
        else:
            resultado_text.value = f"📦 Se encontraron {len(pedidos)} pedido(s):"
            for p in pedidos:
                orden_id, fecha, total, estado = p

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
                pasos = []
                for h_estado, h_fecha in historial:
                    color = {
                        "pendiente": ft.Colors.AMBER_700,
                        "en preparación": ft.Colors.ORANGE,
                        "en camino": ft.Colors.TEAL_700,
                        "entregado": ft.Colors.GREEN,
                    }.get(h_estado, ft.Colors.GREY)
                    pasos.append(
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=color),
                            ft.Text(f"{h_estado.title()} — {h_fecha}", size=13, color=ft.Colors.BLACK)
                        ])
                    )

                color_estado_actual = {
                    "pendiente": ft.Colors.AMBER_700,
                    "en preparación": ft.Colors.ORANGE,
                    "en camino": ft.Colors.TEAL_700,
                    "entregado": ft.Colors.GREEN,
                }.get(estado, ft.Colors.GREY)

                pedidos_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Text(f"Pedido #{orden_id}", size=18, weight="bold", color=ft.Colors.BLACK),
                                ft.Text(f"Fecha: {fecha}", color=ft.Colors.BLACK),
                                ft.Text(f"Total: ${total:.2f}", color=ft.Colors.BLACK),
                                ft.Text(f"Estado actual: {estado.upper()}", color=color_estado_actual, size=16, weight="bold"),
                                ft.Divider(),
                                ft.Text("Historial de estados:", size=14, weight="bold", color=ft.Colors.BLACK),
                                *pasos  # timeline visual
                            ])
                        )
                    )
                )
        page.update()


    def buscar_pedidos(e):
        actualizar_pedidos(telefono_field.value.strip())

    # --- ESCUCHAR NOTIFICACIONES PUBSUB ---
    def recibir_mensaje(data):
        # data = {"telefono": "1234567890", "orden_id": 3, "nuevo_estado": "en camino"}
        tel = telefono_field.value.strip()
        if not tel:
            return
        if data.get("telefono") == tel:
            # Reproducir sonido de campanita (audio mp3 o wav en assets/)
            sound_path = os.path.join(os.path.dirname(__file__), "../../assets/notify.mp3")
            if os.path.exists(sound_path):
                audio = ft.Audio(src=f"/{sound_path}", autoplay=True)
                page.overlay.append(audio)

            page.snack_bar = ft.SnackBar(ft.Text(f"🔔 Tu pedido #{data['orden_id']} ahora está '{data['nuevo_estado']}'"))
            page.snack_bar.open = True
            actualizar_pedidos(tel)

    # Si ya hay un teléfono guardado, cargar pedidos automáticamente
    if telefono_guardado:
        actualizar_pedidos(telefono_guardado)
    pubsub.subscribe(recibir_mensaje)

    return ft.Column([
        ft.Text("📲 Seguimiento de tu pedido", size=24, weight="bold", color=ft.Colors.BLACK),
        ft.Divider(),
        telefono_field,
        ft.ElevatedButton("Buscar pedidos", on_click=buscar_pedidos),
        resultado_text,
        pedidos_list
    ], scroll="auto", expand=True)
