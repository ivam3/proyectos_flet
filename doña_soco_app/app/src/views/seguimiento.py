import flet as ft
import sqlite3
import os
import json
from components.notifier import init_pubsub
from database import obtener_pedido_por_codigo, get_configuracion, actualizar_pago_pedido

DB_PATH = os.path.join(os.path.dirname(__file__), "../../storage/data/dona_soco.db")

def seguimiento_view(page: ft.Page):
    """Pantalla donde el cliente ve y recibe actualizaciones de un pedido específico."""

    pubsub = init_pubsub(page)

    # --- CONFIGURACIÓN ---
    config = get_configuracion()
    contactos = {}
    if config and 'contactos' in config.keys() and config['contactos']:
        try:
            contactos = json.loads(config['contactos'])
        except:
            pass
            
    metodos_pago_config = {"efectivo": True, "terminal": True}
    if config and 'metodos_pago_activos' in config.keys() and config['metodos_pago_activos']:
        try:
            metodos_pago_config = json.loads(config['metodos_pago_activos'])
        except:
            pass

    tipos_tarjeta = []
    if config and 'tipos_tarjeta' in config.keys() and config['tipos_tarjeta']:
        try:
            tipos_tarjeta = json.loads(config['tipos_tarjeta'])
        except:
            pass

    # --- CAMPOS DE BÚSQUEDA ---
    telefono_guardado = getattr(page.session, "telefono_cliente", "")
    telefono_field = ft.TextField(
        label="Tu número de teléfono",
        keyboard_type=ft.KeyboardType.PHONE,
        value=telefono_guardado,
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )
    codigo_field = ft.TextField(
        label="Código de Seguimiento",
        hint_text="Ej: A4T-G8B",
        value=getattr(page.session, "codigo_seguimiento", ""),
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    resultado_container = ft.Column(scroll="auto")

    # --- AYUDA DIALOG ---
    def show_help(e):
        dlg_help = ft.AlertDialog(
            title=ft.Text("Contacto"),
            content=ft.Column([
                ft.Text(f"Teléfono: {contactos.get('telefono', 'N/A')}"),
                ft.Text(f"Email: {contactos.get('email', 'N/A')}"),
                ft.Text(f"Whatsapp: {contactos.get('whatsapp', 'N/A')}"),
                ft.Text(f"Dirección: {contactos.get('direccion', 'N/A')}"),
            ], tight=True),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: setattr(dlg_help, "open", False) or page.update())]
        )
        page.overlay.append(dlg_help)
        dlg_help.open = True
        page.update()

    # --- CAMBIAR PAGO DIALOG ---
    def show_change_payment(e, pedido):
        total = pedido['total']
        
        paga_con_field = ft.TextField(label="¿Con cuánto vas a pagar?", keyboard_type=ft.KeyboardType.NUMBER, prefix=ft.Text("$"), visible=False)
        info_tarjetas = ft.Text(f"Aceptamos: {', '.join(tipos_tarjeta)}", visible=False, size=12, italic=True)

        def on_method_change(e):
            paga_con_field.visible = (e.control.value == "efectivo")
            info_tarjetas.visible = (e.control.value == "terminal")
            page.update()

        opciones = []
        if metodos_pago_config.get("efectivo", True):
            opciones.append(ft.Radio(value="efectivo", label="Efectivo"))
        if metodos_pago_config.get("terminal", True):
            opciones.append(ft.Radio(value="terminal", label="Tarjeta (Terminal)"))

        group = ft.RadioGroup(content=ft.Column(opciones), on_change=on_method_change)

        def save_payment(e):
            if not group.value:
                return
            
            paga_con = 0.0
            if group.value == "efectivo":
                try:
                    paga_con = float(paga_con_field.value)
                    if paga_con < total:
                        page.snack_bar = ft.SnackBar(ft.Text("El monto es menor al total."))
                        page.snack_bar.open = True
                        page.update()
                        return
                except:
                    page.snack_bar = ft.SnackBar(ft.Text("Monto inválido."))
                    page.snack_bar.open = True
                    page.update()
                    return
            
            if actualizar_pago_pedido(pedido['id'], group.value, paga_con):
                dlg_pay.open = False
                page.snack_bar = ft.SnackBar(ft.Text("Método de pago actualizado."))
                page.snack_bar.open = True
                buscar_pedidos(None)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Error al actualizar."))
                page.snack_bar.open = True
                page.update()

        dlg_pay = ft.AlertDialog(
            title=ft.Text("Cambiar Método de Pago"),
            content=ft.Column([
                ft.Text(f"Total a pagar: ${total:.2f}", weight="bold"),
                group,
                paga_con_field,
                info_tarjetas
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg_pay, "open", False) or page.update()),
                ft.FilledButton("Guardar", on_click=save_payment)
            ]
        )
        page.overlay.append(dlg_pay)
        dlg_pay.open = True
        page.update()

    # --- FUNCIÓN PARA ACTUALIZAR PANTALLA ---
    def mostrar_pedido(pedido):
        resultado_container.controls.clear()
        if not pedido:
            resultado_container.controls.append(
                ft.Text("📭 No se encontró ningún pedido con esos datos.", color=ft.Colors.BLACK)
            )
            page.update()
            return

        orden_id = pedido['id']
        fecha = pedido['fecha']
        estado = pedido['estado']
        metodo_pago = pedido['metodo_pago'] or "N/A"
        paga_con = pedido['paga_con'] or 0

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
        
        # Parse products details
        detalles_productos_lista = pedido["detalles_productos"].split(" | ") if pedido["detalles_productos"] else []
        productos_info = ft.Column([ft.Text(f"- {item}", size=13, color=ft.Colors.BLACK) for item in detalles_productos_lista])

        color_estado_actual = {
            "Nuevo": ft.Colors.BLUE_GREY,
            "En preparación": ft.Colors.ORANGE,
            "Listo para entregar": ft.Colors.AMBER,
            "En camino": ft.Colors.TEAL_700,
            "Entregado": ft.Colors.GREEN,
            "Cancelado": ft.Colors.RED_400,
        }.get(estado, ft.Colors.GREY)

        pago_info = ft.Column([
            ft.Text(f"Total a Pagar: ${pedido['total']:.2f}", weight="bold", size=16, color=ft.Colors.GREEN_700),
            ft.Text(f"Método de Pago: {metodo_pago.capitalize()}", weight="bold", color=ft.Colors.BLACK),
            ft.Text(f"Paga con: ${paga_con:.2f}" if metodo_pago == "efectivo" else "", size=12, color=ft.Colors.BLACK)
        ])
        
        can_change_payment = estado not in ["En camino", "Entregado", "Cancelado"]
        btn_change_payment = ft.FilledButton("Cambiar forma de pago", on_click=lambda e: show_change_payment(e, pedido)) if can_change_payment else ft.Container()

        resultado_container.controls.append(
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"Pedido #{orden_id}", size=18, weight="bold", color=ft.Colors.BLACK),
                            ft.IconButton(icon=ft.Icons.HELP_OUTLINE, on_click=show_help, tooltip="Ayuda / Contacto")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Text(f"Fecha: {fecha}", color=ft.Colors.BLACK),
                        ft.Text(f"Estado actual: {estado.upper()}", color=color_estado_actual, size=16, weight="bold"),
                        ft.Text(f"Motivo: {pedido['motivo_cancelacion']}", color=ft.Colors.RED_700, visible=(estado == "Cancelado" and bool(pedido['motivo_cancelacion']))),
                        ft.Divider(),
                        ft.Text("Productos:", weight="bold", color=ft.Colors.BLACK),
                        productos_info,
                        ft.Divider(),
                        pago_info,
                        btn_change_payment,
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
        
        setattr(page.session, "telefono_cliente", tel)
        setattr(page.session, "codigo_seguimiento", codigo)
        
        pedido = obtener_pedido_por_codigo(tel, codigo)
        mostrar_pedido(pedido)
    
    # Auto-search if session data exists
    if getattr(page.session, "telefono_cliente", "") and getattr(page.session, "codigo_seguimiento", ""):
        buscar_pedidos(None)

    # --- ESCUCHAR NOTIFICACIONES PUBSUB ---
    def recibir_mensaje(data):
        tel = telefono_field.value.strip()
        codigo = codigo_field.value.strip().upper()
        
        if not tel or not codigo:
            return
        
        # Si la notificación es para el pedido que se está viendo
        # Obtenemos pedido actual para comparar ID
        pedido_actual = obtener_pedido_por_codigo(tel, codigo)
        if pedido_actual and data.get("telefono") == tel and data.get("orden_id") == pedido_actual["id"]:
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
        ft.Row([
            ft.Button("Buscar pedido", on_click=buscar_pedidos, expand=True),
            ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: buscar_pedidos(None), tooltip="Actualizar estado")
        ]),
        ft.Divider(),
        resultado_container
    ], scroll="auto", expand=True)
