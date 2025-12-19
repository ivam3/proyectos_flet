import flet as ft
from database import guardar_pedido, get_configuracion
from views.menu import cargar_menu
import asyncio
import re

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

    # --- Placeholder para Validación de Dirección ---
    address_validation_status = ft.Row(
        visible=False,
        controls=[
            ft.ProgressRing(width=16, height=16, stroke_width=2),
            ft.Text("Verificando dirección...", style=ft.TextThemeStyle.BODY_SMALL),
        ]
    )

    async def validar_direccion_google(e):
        """Simula validación de dirección."""
        if not all([calle_field.value, colonia_field.value, cp_field.value]):
            return

        address_validation_status.visible = True
        address_validation_status.controls[1].value = "Verificando cobertura..."
        address_validation_status.controls[1].color = ft.Colors.BLACK
        address_validation_status.controls[0].visible = True
        page.update()

        await asyncio.sleep(1.0)
        
        is_valid = True 
        
        address_validation_status.controls[0].visible = False
        if is_valid:
            address_validation_status.controls[1].value = "Dirección válida ✔"
            address_validation_status.controls[1].color = ft.Colors.GREEN_700
            page.update()
            await asyncio.sleep(2.0)
            address_validation_status.visible = False
        else:
            address_validation_status.controls[1].value = "No se pudo verificar la dirección."
            address_validation_status.controls[1].color = ft.Colors.RED_700
        
        page.update()
    
    total = user_cart.get_total()

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
    
    calle_field = ft.TextField(label="Calle y número", border_radius=10, on_blur=validar_direccion_google)
    colonia_field = ft.TextField(label="Colonia", border_radius=10, on_blur=validar_direccion_google)
    
    cp_field = ft.Dropdown(
        label="Código Postal (Zona de Reparto)",
        options=[ft.dropdown.Option(cp) for cp in lista_cps],
        border_radius=10,
        hint_text="Selecciona tu CP",
    )
    cp_field.on_change = validar_direccion_google

    referencias_field = ft.TextField(label="Referencias adicionales", multiline=True, max_lines=2, border_radius=10)

    async def _ir_a_seguimiento(e, codigo, dialog_instance):
        # 1. Cerrar el diálogo usando la instancia específica
        dialog_instance.open = False
        page.update()
        
        # 2. Guardar datos en sesión y limpiar carrito
        user_cart.clear_cart()
        page.session.telefono_cliente = telefono_field.value.strip()
        page.session.codigo_seguimiento = codigo
        
        # 3. Navegar a seguimiento
        await page.push_route("/seguimiento")

    def validar_campos():
        campos_texto = {
            "Nombre": nombre_field, "Teléfono": telefono_field,
            "Calle y número": calle_field, "Colonia": colonia_field
        }
        for nombre, campo in campos_texto.items():
            if not campo.value or not campo.value.strip():
                show_snackbar(f"El campo '{nombre}' es obligatorio.", ft.Colors.AMBER_800)
                return False
        
        if not cp_field.value:
             show_snackbar("Debes seleccionar un Código Postal válido.", ft.Colors.AMBER_800)
             return False

        if not re.match(r"^\d{10}$", telefono_field.value.strip()):
            show_snackbar("El teléfono debe tener 10 dígitos.", ft.Colors.AMBER_800)
            return False
        
        if not metodo_pago_group.value:
            show_snackbar("Selecciona un método de pago.", ft.Colors.AMBER_800)
            return False
            
        if metodo_pago_group.value == "efectivo":
            if not paga_con_field.value:
                show_snackbar("Ingresa con cuánto vas a pagar.", ft.Colors.AMBER_800)
                return False
            try:
                monto = float(paga_con_field.value)
                if monto < total:
                    show_snackbar("El monto no cubre el total del pedido.", ft.Colors.AMBER_800)
                    return False
            except ValueError:
                show_snackbar("Monto inválido.", ft.Colors.AMBER_800)
                return False
            
        return True

    def confirmar_pedido(e):
        if not validar_campos():
            return

        direccion_completa = f"{calle_field.value.strip()}, {colonia_field.value.strip()}, C.P. {cp_field.value}"
        nombre, telefono, referencias = nombre_field.value.strip(), telefono_field.value.strip(), referencias_field.value.strip()
        items = user_cart.get_items()
        
        metodo = metodo_pago_group.value
        paga_con = float(paga_con_field.value) if metodo == "efectivo" else 0.0
        
        exito, codigo_seguimiento = guardar_pedido(nombre, telefono, direccion_completa, referencias, total, items, metodo, paga_con)

        dlg_content = ft.Column([
                ft.Text("Tu pedido ha sido enviado correctamente."),
                ft.Text("Usa este código para darle seguimiento:"),
                ft.Text(f"{codigo_seguimiento}", weight=ft.FontWeight.BOLD, size=20, selectable=True),
            ]) if exito else ft.Text("Ocurrió un error al guardar tu pedido. Por favor, intenta de nuevo.")
        
        # Definimos el diálogo
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("✅ Pedido Registrado" if exito else "❌ Error en el Pedido"),
            content=dlg_content,
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Definimos la acción del botón Aceptar
        async def on_accept(ev):
            if exito:
                await _ir_a_seguimiento(ev, codigo_seguimiento, dlg)
            else:
                dlg.open = False
                page.update()

        dlg.actions = [ft.FilledButton(content=ft.Text("Aceptar"), on_click=on_accept)]

        # USAMOS OVERLAY PARA ASEGURAR VISIBILIDAD
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    if not lista_cps:
        cp_field.disabled = True
        cp_field.label = "No hay zonas de reparto configuradas"
        cp_field.error_text = "Contacte al administrador"

    return ft.Column(
        controls=[
            ft.Text("Datos de Entrega", size=24, weight="bold"),
            ft.Divider(height=10),
            nombre_field,
            telefono_field,
            calle_field,
            colonia_field,
            cp_field,
            address_validation_status,
            referencias_field,
            
            ft.Divider(height=20),
            ft.Text("Método de Pago", size=18, weight="bold"),
            metodo_pago_group,
            paga_con_field,
            info_tarjetas,
            
            ft.Divider(height=20),
            ft.ListTile(
                title=ft.Text("Total a Pagar:", weight=ft.FontWeight.BOLD),
                trailing=ft.Text(f"${total:.2f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
            ),
            ft.FilledButton(
                content=ft.Text("Confirmar Pedido"), icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                on_click=confirmar_pedido, width=float('inf')
            )
        ],
        scroll=ft.ScrollMode.ADAPTIVE, spacing=15, expand=True,
    )
