import flet as ft
import os
import json
import datetime
from fpdf import FPDF
from config import COMPANY_NAME
from components.notifier import init_pubsub, show_notification
from database import obtener_pedido_por_codigo, get_configuracion, actualizar_pago_pedido, actualizar_estado_pedido

# Adjust path to DB relative to src/views
# ... (rest of comments)

def seguimiento_view(page: ft.Page):
    """Pantalla donde el cliente ve y recibe actualizaciones de un pedido específico."""

    pubsub = init_pubsub(page)
    
    # --- LÓGICA DE PLATAFORMA ---
    plat = str(page.platform).lower() if page.platform else ""
    # Forzar modo móvil si la plataforma contiene 'android' o 'ios', ignorando page.web
    es_movil = "android" in plat or "ios" in plat
    es_escritorio_o_web = (page.web or plat in ["windows", "macos", "linux"]) and not es_movil
    
    print(f"DEBUG: Iniciando Seguimiento | Plataforma: {plat} | Es Movil: {es_movil} | Modo Web/Desktop activo: {es_escritorio_o_web}")

    # --- LÓGICA PDF Y ARCHIVOS ---
    export_file_picker = None

    def on_file_picker_result(e):
        if e.path:
             show_notification(page, f"Archivo guardado exitosamente.", ft.Colors.GREEN)
        else:
             show_notification(page, "Operación cancelada.", ft.Colors.GREY_700)
        page.update()

    # SOLO agregamos el FilePicker si estamos en Desktop/Web
    if es_escritorio_o_web:
        print("DEBUG: Inicializando FilePicker (Entorno Web/Escritorio)")
        export_file_picker = ft.FilePicker()
        export_file_picker.on_result = on_file_picker_result
        # Usamos un contenedor casi invisible (1x1 px) pero técnicamente visible para el DOM web
        page.overlay.append(ft.Container(content=export_file_picker, width=1, height=1, opacity=0))
    else:
        print("DEBUG: Omitiendo FilePicker (Entorno Android/Móvil Nativo)")

    error_dialog = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text(""))
    success_dialog = ft.AlertDialog(
        title=ft.Text("Descarga Exitosa", color=ft.Colors.GREEN), 
        content=ft.Text(""),
        actions=[ft.TextButton("Aceptar", on_click=lambda e: cerrar_dialogos())]
    )
    page.overlay.extend([error_dialog, success_dialog])

    def cerrar_dialogos():
        error_dialog.open = False
        success_dialog.open = False
        page.update()

    def mostrar_error(msg):
        error_dialog.content.value = str(msg)
        error_dialog.open = True
        page.update()

    def mostrar_exito_android(ruta):
        success_dialog.content.value = f"El archivo se ha guardado correctamente en:\n\n{ruta}"
        success_dialog.open = True
        page.update()

    def guardar_archivo_android(filename, content_bytes):
        rutas_a_probar = []
        rutas_a_probar.append(os.path.join("/storage/emulated/0/Download", filename))
        rutas_a_probar.append(os.path.join(os.getcwd(), filename))

        guardado = False
        ruta_final = ""

        for ruta in rutas_a_probar:
            try:
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "wb") as f:
                    f.write(content_bytes)
                guardado = True
                ruta_final = ruta
                break
            except Exception as e:
                continue

        if guardado:
            mostrar_exito_android(ruta_final)
        else:
            mostrar_error("No se pudo guardar el archivo. Verifique permisos de almacenamiento.")

    async def generar_y_guardar_pdf(pedido):
        print(f"DEBUG: Iniciando generación PDF para pedido {pedido['id']}")
        show_notification(page, "Generando PDF...", ft.Colors.BLUE_GREY_700)

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size=12)
            pdf.set_margins(10, 10, 10)
            
            pdf.set_font("helvetica", 'B', 16)
            pdf.cell(0, 10, text=f"Comprobante - {COMPANY_NAME}", align='C', new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=14)
            pdf.cell(0, 10, text=f"Pedido #{pedido['id']}", align='C', new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 10, text=f"Fecha: {pedido['fecha']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 10, text=f"Código: {pedido['codigo_seguimiento']}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", 'B', 14)
            pdf.cell(0, 10, text="Datos del Cliente", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 8, text=f"Nombre: {pedido['nombre_cliente']}", new_x="LMARGIN", new_y="NEXT")
            
            direccion = (pedido['direccion'] or "").encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(w=pdf.epw, h=8, text=f"Dirección: {direccion}")
            pdf.ln(5)
            
            pdf.set_font("helvetica", 'B', 14)
            pdf.cell(0, 10, text="Productos", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=11)
            
            detalles = pedido["detalles_productos"].split(" | ") if pedido.get("detalles_productos") else []
            for item in detalles:
                safe_item = item.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(w=pdf.epw, h=7, text=f"- {safe_item}", border=0, align='L')
                pdf.ln(1)
            
            pdf.ln(5)
            pdf.set_font("helvetica", 'B', 16)
            pdf.cell(0, 10, text=f"Total: ${pedido['total']:.2f}", align='R', new_x="LMARGIN", new_y="NEXT")

            pdf_bytes = bytes(pdf.output())
            
            filename = f"pedido_{pedido['id']}.pdf"
            
            # --- SELECTOR DE ESTRATEGIA (Usando banderas pre-calculadas) ---
            print(f"DEBUG: Ejecutando estrategia para plataforma: {plat} | Web/Desktop: {es_escritorio_o_web}")

            if es_escritorio_o_web:
                if export_file_picker:
                    print("DEBUG: Usando FilePicker (Web/Escritorio)")
                    await export_file_picker.save_file(
                        dialog_title=f"Guardar PDF #{pedido['id']}",
                        file_name=filename,
                        allowed_extensions=["pdf"],
                        src_bytes=pdf_bytes
                    )
                else:
                    print("DEBUG ERROR: Se detectó Desktop pero export_file_picker es None")
                    mostrar_error("Error interno: Selector de archivos no inicializado.")
            else:
                print("DEBUG: Usando Escritura Directa (Android/Móvil)")
                guardar_archivo_android(filename, pdf_bytes)
            
        except Exception as ex:
             print(f"DEBUG ERROR en PDF: {ex}")
             mostrar_error(f"Error PDF: {ex}")

    def create_pdf_handler(pedido):
        async def handler(e):
            print(f"DEBUG: Click recibido en botón PDF para pedido {pedido.get('id')}")
            try:
                await generar_y_guardar_pdf(pedido)
            except Exception as ex:
                print(f"DEBUG: Error al invocar generar_y_guardar_pdf: {ex}")
        return handler

    def show_cancel_order(e, pedido):
        reason_field = ft.TextField(label="¿Por qué deseas cancelar?", multiline=True, hint_text="Ej: Me equivoqué de platillo...", text_style=ft.TextStyle(color=ft.Colors.BLACK))

        def confirm_cancel(e):
            if not reason_field.value.strip():
                reason_field.error_text = "Por favor, ingresa el motivo."
                reason_field.update()
                return
            
            if actualizar_estado_pedido(pedido['id'], "Cancelado", reason_field.value.strip()):
                dlg_cancel.open = False
                show_notification(page, "Pedido cancelado exitosamente.", ft.Colors.GREEN)
                buscar_pedidos(None)
            else:
                show_notification(page, "Error al cancelar el pedido.", ft.Colors.RED)
                page.update()

        dlg_cancel = ft.AlertDialog(
            title=ft.Text("Confirmar Cancelación", color=ft.Colors.BLACK),
            content=ft.Column([
                ft.Text(f"¿Estás seguro de cancelar el pedido #{pedido['id']}?", color=ft.Colors.BLACK),
                reason_field
            ], tight=True),
            actions=[
                ft.TextButton("Volver", on_click=lambda e: setattr(dlg_cancel, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700)),
                ft.FilledButton(
                    "Confirmar Cancelación", 
                    on_click=confirm_cancel, 
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                )
            ]
        )
        page.overlay.append(dlg_cancel)
        dlg_cancel.open = True
        page.update()

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

    telefono_guardado = getattr(page.session, "telefono_cliente", "")
    telefono_field = ft.TextField(
        label="Tu número de teléfono",
        keyboard_type=ft.KeyboardType.PHONE,
        value=telefono_guardado,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        text_style=ft.TextStyle(color=ft.Colors.BLACK)
    )
    codigo_field = ft.TextField(
        label="Código de Seguimiento",
        hint_text="Ej: A4T-G8B",
        value=getattr(page.session, "codigo_seguimiento", ""),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        text_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    resultado_container = ft.Column(scroll="auto")

    def show_help(e):
        dlg_help = ft.AlertDialog(
            title=ft.Text("Contacto", color=ft.Colors.BLACK),
            content=ft.Column([
                ft.Text(f"Teléfono: {contactos.get('telefono', 'N/A')}", color=ft.Colors.BLACK),
                ft.Text(f"Email: {contactos.get('email', 'N/A')}", color=ft.Colors.BLACK),
                ft.Text(f"Whatsapp: {contactos.get('whatsapp', 'N/A')}", color=ft.Colors.BLACK),
                ft.Text(f"Dirección: {contactos.get('direccion', 'N/A')}", color=ft.Colors.BLACK),
            ], tight=True),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: setattr(dlg_help, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700))]
        )
        page.overlay.append(dlg_help)
        dlg_help.open = True
        page.update()

    def show_change_payment(e, pedido):
        total = pedido['total']
        
        paga_con_field = ft.TextField(label="¿Con cuánto vas a pagar?", keyboard_type=ft.KeyboardType.NUMBER, prefix=ft.Text("$", color=ft.Colors.BLACK), visible=False, text_style=ft.TextStyle(color=ft.Colors.BLACK))
        info_tarjetas = ft.Text(f"Aceptamos: {', '.join(tipos_tarjeta)}", visible=False, size=12, italic=True, color=ft.Colors.BLACK)

        def on_method_change(e):
            paga_con_field.visible = (e.control.value == "efectivo")
            info_tarjetas.visible = (e.control.value == "terminal")
            page.update()

        opciones = []
        if metodos_pago_config.get("efectivo", True):
            opciones.append(ft.Radio(value="efectivo", label="Efectivo")) # Radio label inherits theme, usually ok
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
                        show_notification(page, "El monto es menor al total.", ft.Colors.RED)
                        page.update()
                        return
                except:
                    show_notification(page, "Monto inválido.", ft.Colors.RED)
                    page.update()
                    return
            
            if actualizar_pago_pedido(pedido['id'], group.value, paga_con):
                dlg_pay.open = False
                show_notification(page, "Método de pago actualizado.", ft.Colors.GREEN)
                buscar_pedidos(None)
            else:
                show_notification(page, "Error al actualizar.", ft.Colors.RED)
                page.update()

        dlg_pay = ft.AlertDialog(
            title=ft.Text("Cambiar Método de Pago", color=ft.Colors.BLACK),
            content=ft.Column([
                ft.Text(f"Total a pagar: ${total:.2f}", weight="bold", color=ft.Colors.BLACK),
                group,
                paga_con_field,
                info_tarjetas
            ], tight=True),
            actions=[
                ft.TextButton("Volver", on_click=lambda e: setattr(dlg_pay, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700)),
                ft.FilledButton(
                    "Guardar", 
                    on_click=save_payment,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
                )
            ]
        )
        page.overlay.append(dlg_pay)
        dlg_pay.open = True
        page.update()

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

        # Obtener historial directamente del objeto pedido (API)
        historial = pedido.get('historial', [])

        pasos = [
            ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREY),
                ft.Text(f"{h.get('nuevo_estado', '').title()} — {h.get('fecha', '')}", size=13, color=ft.Colors.BLACK)
            ]) for h in historial
        ]
        
        detalles_productos_lista = pedido["detalles_productos"].split(" | ") if pedido["detalles_productos"] else []
        productos_info = ft.Column([ft.Text(f"- {item}", size=13, color=ft.Colors.BLACK) for item in detalles_productos_lista])

        color_estado_actual = {
            "Pendiente": ft.Colors.BLUE_GREY,
            "Preparando": ft.Colors.ORANGE,
            "Listo para entregar": ft.Colors.AMBER,
            "En Camino": ft.Colors.TEAL_700,
            "Entregado": ft.Colors.GREEN,
            "Cancelado": ft.Colors.RED_400,
        }.get(estado, ft.Colors.GREY)

        pago_info = ft.Column([
            ft.Text(f"Total a Pagar: ${pedido['total']:.2f}", weight="bold", size=16, color=ft.Colors.GREEN_700),
            ft.Text(f"Método de Pago: {metodo_pago.capitalize()}", weight="bold", color=ft.Colors.BLACK),
            ft.Text(f"Paga con: ${paga_con:.2f}" if metodo_pago == "efectivo" else "", size=12, color=ft.Colors.BLACK)
        ])
        
        can_change_payment = estado in ["Pendiente", "Preparando"]
        btn_change_payment = ft.FilledButton(
            "Cambiar forma de pago", 
            on_click=lambda e: show_change_payment(e, pedido),
            style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
        ) if can_change_payment else ft.Container()

        can_cancel = estado in ["Pendiente", "Nuevo"]
        btn_cancel = ft.FilledButton(
            "Cancelar pedido", 
            on_click=lambda e: show_cancel_order(e, pedido), 
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
        ) if can_cancel else ft.Container()

        resultado_container.controls.append(
            ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"Pedido #{orden_id}", size=18, weight="bold", color=ft.Colors.BLACK),
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.PICTURE_AS_PDF, 
                                    tooltip="Descargar Comprobante", 
                                    icon_color=ft.Colors.RED_700, 
                                    on_click=create_pdf_handler(pedido)
                                ),
                                ft.IconButton(icon=ft.Icons.HELP_OUTLINE, on_click=show_help, tooltip="Ayuda / Contacto", icon_color=ft.Colors.BLACK)
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Text(f"Fecha: {fecha}", color=ft.Colors.BLACK),
                        ft.Text(f"Estado actual: {estado.upper()}", color=color_estado_actual, size=16, weight="bold"),
                        ft.Text(f"Motivo: {pedido.get('motivo_cancelacion', '')}", color=ft.Colors.RED_700, visible=(estado == "Cancelado" and bool(pedido.get('motivo_cancelacion')))),
                        ft.Divider(),
                        ft.Text("Productos:", weight="bold", color=ft.Colors.BLACK),
                        productos_info,
                        ft.Divider(),
                        pago_info,
                        ft.Column([btn_change_payment, btn_cancel], spacing=10),
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
            show_notification(page, "Por favor, ingresa el teléfono y el código de seguimiento.", ft.Colors.ORANGE)
            page.update()
            return
        
        setattr(page.session, "telefono_cliente", tel)
        setattr(page.session, "codigo_seguimiento", codigo)
        
        pedido = obtener_pedido_por_codigo(tel, codigo)
        mostrar_pedido(pedido)
    
    if getattr(page.session, "telefono_cliente", "") and getattr(page.session, "codigo_seguimiento", ""):
        buscar_pedidos(None)

    def recibir_mensaje(data):
        tel = telefono_field.value.strip()
        codigo = codigo_field.value.strip().upper()
        
        if not tel or not codigo:
            return
        
        pedido_actual = obtener_pedido_por_codigo(tel, codigo)
        if pedido_actual and data.get("telefono") == tel and data.get("orden_id") == pedido_actual["id"]:
            # Sound logic... (simplified for now)
            pass

            show_notification(page, f"🔔 Tu pedido #{data['orden_id']} ahora está '{data['nuevo_estado']}'", ft.Colors.BLUE)
            buscar_pedidos(None)

    pubsub.subscribe(recibir_mensaje)

    return ft.Column([
        ft.Text("📲 Seguimiento de tu pedido", size=24, weight="bold", color=ft.Colors.BLACK),
        ft.Divider(),
        telefono_field,
        codigo_field,
        ft.Row([
            ft.FilledButton(
                content=ft.Text("Buscar pedido"), 
                on_click=buscar_pedidos, 
                expand=True,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
            ),
            ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: buscar_pedidos(None), tooltip="Actualizar estado")
        ]),
        ft.Divider(),
        resultado_container
    ], scroll="auto", expand=True)
