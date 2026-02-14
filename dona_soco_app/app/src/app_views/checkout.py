import flet as ft
from database import guardar_pedido, get_configuracion
from app_views.menu import cargar_menu
from components.notifier import init_pubsub # Importar notifier
import asyncio
import re
import httpx

def create_checkout_view(page: ft.Page, show_snackbar, nav):
    """Pantalla donde el usuario ingresa sus datos de envío antes de confirmar el pedido."""
    
    user_cart = page.session.cart

    # --- Configuración de Códigos Postales y Pagos ---
    config = get_configuracion()
    # Procesar la cadena "12345, 67890" a una lista ["12345", "67890"]
    raw_cps = config['codigos_postales'] if config and config['codigos_postales'] else ""
    lista_cps = [cp.strip() for cp in raw_cps.split(',') if cp.strip()]
    
    import json
    metodos_pago = {"efectivo": True, "terminal": True}
    if config and 'metodos_pago_activos' in config.keys() and config['metodos_pago_activos']:
        try:
            metodos_pago = json.loads(config['metodos_pago_activos'])
        except:
            pass
            
    tipos_tarjeta = []
    if config and 'tipos_tarjeta' in config.keys() and config['tipos_tarjeta']:
        try:
            tipos_tarjeta = json.loads(config['tipos_tarjeta'])
        except:
            pass

    # --- Función de Validación ---
    async def validar_direccion_google(e):
        """Valida la dirección usando OpenStreetMap (Gratis)."""
        if not calle_field.value or not cp_field.value:
            return

        calle_field.helper = "Verificando dirección..."
        calle_field.helper_style = ft.TextStyle(color=ft.Colors.BLUE_GREY_700)
        page.update()

        try:
            query = f"{calle_field.value}, {cp_field.value}, Mexico"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": query, "format": "json", "limit": 1},
                    headers={"User-Agent": "DonaSocoApp/1.0"}
                )
                data = response.json()

            if data and len(data) > 0:
                calle_field.helper = "Dirección localizada ✔"
                calle_field.helper_style = ft.TextStyle(color=ft.Colors.GREEN_700)
                show_snackbar("Dirección localizada correctamente ✔", ft.Colors.GREEN_700)
            else:
                calle_field.helper = "No se encontró la ubicación exacta."
                calle_field.helper_style = ft.TextStyle(color=ft.Colors.ORANGE_800)
                show_snackbar("No pudimos localizar la dirección exacta, por favor verifica.", ft.Colors.ORANGE_800)
        
        except Exception as ex:
            calle_field.helper = "Error al conectar con el servicio de mapas."
            calle_field.helper_style = ft.TextStyle(color=ft.Colors.RED_700)
        
        page.update()
    
    total = user_cart.get_total()
    COSTO_ENVIO = 20.0
    # total_final = total + COSTO_ENVIO  <-- Eliminado, ahora es dinámico

    # Variables visuales para totales
    txt_envio = ft.Text(f"${COSTO_ENVIO:.2f}")
    txt_total = ft.Text(f"${(total + COSTO_ENVIO):.2f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)

    # --- CAMPOS DE PAGO ---
    paga_con_field = ft.TextField(label="¿Con cuánto vas a pagar?", keyboard_type=ft.KeyboardType.NUMBER, prefix=ft.Text("$"), visible=False, border_radius=10)
    info_tarjetas = ft.Text(f"Aceptamos: {', '.join(tipos_tarjeta)}", visible=False, color=ft.Colors.BLUE_GREY_700, italic=True)

    def on_metodo_pago_change(e):
        paga_con_field.visible = (e.control.value == "efectivo")
        info_tarjetas.visible = (e.control.value == "terminal")
        page.update()

    opciones_pago = []
    if metodos_pago.get("efectivo", True):
        opciones_pago.append(ft.Radio(value="efectivo", label="Efectivo"))
    if metodos_pago.get("terminal", True):
        opciones_pago.append(ft.Radio(value="terminal", label="Tarjeta (Terminal física)"))

    metodo_pago_group = ft.RadioGroup(
        content=ft.Column(opciones_pago),
        on_change=on_metodo_pago_change
    )

    # --- CAMPOS DEL FORMULARIO ---
    nombre_field = ft.TextField(label="Nombre completo", autofocus=True, border_radius=10)
    telefono_field = ft.TextField(label="Teléfono de contacto", keyboard_type=ft.KeyboardType.PHONE, border_radius=10)
    
    calle_field = ft.TextField(
        label="Calle y número", 
        border_radius=10, 
        on_blur=validar_direccion_google,
        helper="Ingresa calle y número para validar"
    )
    colonia_field = ft.TextField(label="Colonia", border_radius=10, on_blur=validar_direccion_google)
    
    cp_field = ft.Dropdown(
        label="Código Postal (Zona de Reparto)",
        options=[ft.dropdown.Option(cp) for cp in lista_cps],
        border_radius=10,
        hint_text="Selecciona tu CP",
        on_select=validar_direccion_google
    )

    referencias_field = ft.TextField(label="Referencias adicionales", multiline=True, max_lines=2, border_radius=10)

    async def _ir_a_seguimiento(e, codigo, dialog_instance):
        # 1. Guardar datos en sesión y limpiar carrito
        page.session.telefono_cliente = telefono_field.value.strip()
        page.session.codigo_seguimiento = codigo
        user_cart.clear_cart()
        
        # 2. Cerrar el diálogo
        dialog_instance.open = False
        
        # 3. Forzar cambio visual inmediato
        from app_views.seguimiento import seguimiento_view
        nav.selected_index = 2
        
        # Intentamos encontrar el contenedor de contenido en el layout
        # Basado en main.py: page.add(top_bar, content_area, nav, picker_shield)
        # content_area es el control en el índice 1
        try:
            page.controls[1].content = seguimiento_view(page)
        except:
            pass # Si falla por índice, al menos intentamos la ruta
            
        await page.push_route("/seguimiento")
        page.update()

    # --- LOGICA RECOGER EN TIENDA ---
    def on_pickup_change(e):
        is_pickup = pickup_checkbox.value
        
        # Ocultar/Mostrar campos de dirección
        calle_field.visible = not is_pickup
        colonia_field.visible = not is_pickup
        cp_field.visible = not is_pickup
        referencias_field.visible = not is_pickup
        
        # Actualizar costos
        costo_actual = 0.0 if is_pickup else COSTO_ENVIO
        total_actual = total + costo_actual
        
        txt_envio.value = f"${costo_actual:.2f}"
        txt_total.value = f"${total_actual:.2f}"
        
        page.update()

    pickup_checkbox = ft.Checkbox(label="Recoger en restaurante (Sin costo de envío)", on_change=on_pickup_change)

    # --- Función de Alerta Popup ---
    def mostrar_alerta(mensaje):
        dlg_alert = ft.AlertDialog(
            title=ft.Text("Dato faltante o erróneo"),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Entendido", on_click=lambda e: setattr(dlg_alert, "open", False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.BROWN_700))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg_alert)
        dlg_alert.open = True
        page.update()

    def validar_campos():
        # Validar Nombre y Teléfono siempre
        if not nombre_field.value or not nombre_field.value.strip():
            mostrar_alerta("El campo 'Nombre' es obligatorio.")
            return False
        if not telefono_field.value or not telefono_field.value.strip():
            mostrar_alerta("El campo 'Teléfono' es obligatorio.")
            return False
            
        # Si NO es pickup, validar dirección
        if not pickup_checkbox.value:
            if not calle_field.value or not calle_field.value.strip():
                 mostrar_alerta("El campo 'Calle y número' es obligatorio.")
                 return False
            if not colonia_field.value or not colonia_field.value.strip():
                 mostrar_alerta("El campo 'Colonia' es obligatorio.")
                 return False
            if not cp_field.value:
                 mostrar_alerta("Debes seleccionar un Código Postal válido.")
                 return False

        if not re.match(r"^\d{10}$", telefono_field.value.strip()):
            mostrar_alerta("El teléfono debe tener 10 dígitos.")
            return False
        
        if not metodo_pago_group.value:
            mostrar_alerta("Selecciona un método de pago.")
            return False
            
        # Recalcular total actual
        costo_envio_actual = 0.0 if pickup_checkbox.value else COSTO_ENVIO
        total_actual_validacion = total + costo_envio_actual

        if metodo_pago_group.value == "efectivo":
            if not paga_con_field.value:
                mostrar_alerta("Ingresa con cuánto vas a pagar.")
                return False
            try:
                monto = float(paga_con_field.value)
                if monto < total_actual_validacion:
                    mostrar_alerta("El monto no cubre el total del pedido.")
                    return False
            except ValueError:
                mostrar_alerta("Monto inválido.")
                return False
            
        return True

    async def confirmar_pedido(e):
        try:
            btn_confirmar.disabled = True
            btn_confirmar.text = "Procesando..."
            page.update()

            if not validar_campos():
                btn_confirmar.disabled = False
                btn_confirmar.text = "Confirmar Pedido"
                page.update()
                return

            items = user_cart.get_items()
            if not items:
                show_snackbar("El carrito está vacío.", ft.Colors.RED)
                # Volver al carrito o navegar
                nav.selected_index = 1
                await page.push_route("/carrito") 
                return

            if pickup_checkbox.value:
                direccion_completa = "Entrega en restaurante"
                total_final_confirm = total # Sin envío
            else:
                direccion_completa = f"{calle_field.value.strip()}, {colonia_field.value.strip()}, C.P. {cp_field.value}"
                total_final_confirm = total + COSTO_ENVIO

            nombre, telefono, referencias = nombre_field.value.strip(), telefono_field.value.strip(), referencias_field.value.strip()
            
            metodo = metodo_pago_group.value
            paga_con = float(paga_con_field.value) if metodo == "efectivo" else 0.0
            
            exito, codigo_seguimiento = guardar_pedido(nombre, telefono, direccion_completa, referencias, total_final_confirm, items, metodo, paga_con)

            if exito:
                # Enviar notificación en tiempo real a los admins
                try:
                    pubsub = init_pubsub(page)
                    pubsub.send_all("nuevo_pedido")
                except Exception as e:
                    print(f"Error enviando notificacion: {e}")

            dlg_content = ft.Column([
                    ft.Text("Tu pedido ha sido enviado correctamente."),
                    ft.Text("Usa este código para darle seguimiento:"),
                    ft.Text(f"{codigo_seguimiento}", weight=ft.FontWeight.BOLD, size=20, selectable=True, text_align=ft.TextAlign.CENTER),
                ], tight=True, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER) if exito else ft.Text("Ocurrió un error al guardar tu pedido. Por favor, intenta de nuevo.")
            
            # Definimos el diálogo
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("✅ Pedido Registrado" if exito else "❌ Error en el Pedido"),
                content=ft.Container(content=dlg_content, width=300, padding=10),
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(radius=10),
            )

            # Definimos la acción del botón Aceptar
            async def on_accept(ev):
                if exito:
                    await _ir_a_seguimiento(ev, codigo_seguimiento, dlg)
                else:
                    dlg.open = False
                    btn_confirmar.disabled = False # Re-enable if error
                    btn_confirmar.text = "Confirmar Pedido"
                    page.update()

            dlg.actions = [ft.FilledButton(content=ft.Text("Aceptar"), on_click=on_accept, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE))]

            # USAMOS OVERLAY PARA ASEGURAR VISIBILIDAD
            page.overlay.append(dlg)
            dlg.open = True
            page.update()
        except Exception as ex:
            print(f"ERROR CRÍTICO CHECKOUT: {ex}")
            show_snackbar(f"Error al procesar pedido: {ex}", ft.Colors.RED)
            btn_confirmar.disabled = False
            btn_confirmar.text = "Confirmar Pedido"
            page.update()

    if not lista_cps:
        cp_field.disabled = True
        cp_field.label = "No hay zonas de reparto configuradas"
        cp_field.error_text = "Contacte al administrador"

    btn_confirmar = ft.FilledButton(
        content=ft.Text("Confirmar Pedido"), 
        icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
        on_click=confirmar_pedido, 
        width=float('inf'),
        style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
    )

    return ft.Column(
        controls=[
            ft.Text("Datos de Entrega", size=24, weight="bold"),
            ft.Divider(height=10),
            pickup_checkbox,
            nombre_field,
            telefono_field,
            calle_field,
            colonia_field,
            cp_field,
            referencias_field,
            
            ft.Divider(height=20),
            ft.Text("Método de Pago", size=18, weight="bold"),
            metodo_pago_group,
            paga_con_field,
            info_tarjetas,
            
            ft.Divider(height=20),
            ft.Column([
                ft.Row([ft.Text("Subtotal:", weight=ft.FontWeight.BOLD), ft.Text(f"${total:.2f}")] , alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Envío:", weight=ft.FontWeight.BOLD), txt_envio] , alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ListTile(
                    title=ft.Text("Total a Pagar:", weight=ft.FontWeight.BOLD, size=18),
                    trailing=txt_total,
                )
            ]),
            btn_confirmar
        ],
        scroll=ft.ScrollMode.ADAPTIVE, spacing=15, expand=True,
    )
