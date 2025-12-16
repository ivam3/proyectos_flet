import flet as ft
from database import guardar_pedido, get_configuracion
from views.menu import cargar_menu

from views.seguimiento import seguimiento_view

def create_checkout_view(page: ft.Page, show_snackbar, nav):
    """Pantalla donde el usuario ingresa sus datos de envío antes de confirmar el pedido."""
    import re
    import time

    user_cart = page.session.cart

    # --- Placeholder para Validación de Dirección ---
    address_validation_status = ft.Row(
        visible=False,
        controls=[
            ft.ProgressRing(width=16, height=16, stroke_width=2),
            ft.Text("Verificando dirección...", style=ft.TextThemeStyle.BODY_SMALL),
        ]
    )

    def validar_direccion_google(e):
        """
        Placeholder para la validación de dirección con una API externa como Google.
        Se activa cuando el usuario sale de un campo de dirección.
        """
        # Solo procede si hay datos en los campos clave de dirección
        if not all([calle_field.value, colonia_field.value, cp_field.value]):
            return

        address_validation_status.visible = True
        address_validation_status.controls[1].value = "Verificando dirección..."
        address_validation_status.controls[1].color = ft.Colors.BLACK
        address_validation_status.controls[0].visible = True # Muestra el anillo de progreso
        page.update()

        # >>> INICIO DEL MARCADOR DE POSICIÓN <<<
        # Aquí iría la llamada a la API de Google Address Validation.
        # Se simulará una demora de 1.5 segundos.
        time.sleep(1.5)
        # Basado en la respuesta de la API, se actualizaría el estado.
        # Simulamos una validación exitosa.
        is_valid = True 
        # >>> FIN DEL MARCADOR DE POSICIÓN <<<
        
        address_validation_status.controls[0].visible = False # Oculta el anillo de progreso
        if is_valid:
            address_validation_status.controls[1].value = "Dirección verificada (simulado) ✔"
            address_validation_status.controls[1].color = ft.Colors.GREEN_700
        else:
            address_validation_status.controls[1].value = "No se pudo verificar la dirección."
            address_validation_status.controls[1].color = ft.Colors.RED_700
        page.update()

    # --- CAMPOS DEL FORMULARIO ---
    nombre_field = ft.TextField(label="Nombre completo", autofocus=True, border_radius=10)
    telefono_field = ft.TextField(label="Teléfono de contacto", keyboard_type=ft.KeyboardType.PHONE, border_radius=10)
    calle_field = ft.TextField(label="Calle y número", border_radius=10, on_blur=validar_direccion_google)
    colonia_field = ft.TextField(label="Colonia", border_radius=10, on_blur=validar_direccion_google)
    cp_field = ft.TextField(label="Código Postal", keyboard_type=ft.KeyboardType.NUMBER, max_length=5, border_radius=10, on_blur=validar_direccion_google)
    referencias_field = ft.TextField(label="Referencias adicionales", multiline=True, max_lines=2, border_radius=10)

    total = user_cart.get_total()

    def _ir_a_seguimiento(codigo):
        user_cart.clear_cart()
        page.session.telefono_cliente = telefono_field.value.strip()
        page.session.codigo_seguimiento = codigo
        page.go("/seguimiento")

    def validar_campos():
        campos = {
            "Nombre": nombre_field, "Teléfono": telefono_field,
            "Calle y número": calle_field, "Colonia": colonia_field, 
            "Código Postal": cp_field
        }
        for nombre, campo in campos.items():
            if not campo.value or not campo.value.strip():
                show_snackbar(f"El campo '{nombre}' es obligatorio.", ft.Colors.AMBER_800)
                return False
        if not re.match(r"^\d{10}$", telefono_field.value.strip()):
            show_snackbar("El teléfono debe tener 10 dígitos.", ft.Colors.AMBER_800)
            return False
        if not re.match(r"^\d{5}$", cp_field.value.strip()):
            show_snackbar("El Código Postal debe tener 5 dígitos.", ft.Colors.AMBER_800)
            return False
        return True

    def mostrar_dialogo_error_cp():
        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("📍 Fuera de Zona de Reparto"),
            content=ft.Text("Lo sentimos, tu código postal se encuentra fuera de nuestra área de servicio actual."),
            actions=[ft.TextButton(content=ft.Text("Entendido"), on_click=lambda e: setattr(e.control.page.dialog, "open", False) or e.control.page.update())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def confirmar_pedido(e):
        if not validar_campos():
            return

        config = get_configuracion()
        codigos_permitidos = [cp.strip() for cp in config['codigos_postales'].split(',')] if config and config['codigos_postales'] else []
        if cp_field.value.strip() not in codigos_permitidos:
            mostrar_dialogo_error_cp()
            return
        
        direccion_completa = f"{calle_field.value.strip()}, {colonia_field.value.strip()}, C.P. {cp_field.value.strip()}"
        nombre, telefono, referencias = nombre_field.value.strip(), telefono_field.value.strip(), referencias_field.value.strip()
        items = user_cart.get_items()
        
        exito, codigo_seguimiento = guardar_pedido(nombre, telefono, direccion_completa, referencias, total, items)

        dlg_content = ft.Column([
                ft.Text("Tu pedido ha sido enviado correctamente."),
                ft.Text("Usa este código para darle seguimiento:"),
                ft.Text(f"{codigo_seguimiento}", weight=ft.FontWeight.BOLD, size=20, selectable=True),
            ]) if exito else ft.Text("Ocurrió un error al guardar tu pedido. Por favor, intenta de nuevo.")
        
        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("✅ Pedido Registrado" if exito else "❌ Error en el Pedido"),
            content=dlg_content,
            actions=[ft.FilledButton(content=ft.Text("Aceptar"), on_click=lambda e: _ir_a_seguimiento(codigo_seguimiento) if exito else setattr(e.control.page.dialog, "open", False) or e.control.page.update())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    return ft.Column(
        controls=[
            ft.Text("Datos de Entrega", size=24, weight="bold"),
            ft.Divider(height=10),
            nombre_field,
            telefono_field,
            calle_field,
            colonia_field,
            cp_field,
            address_validation_status, # Indicador de validación de dirección
            referencias_field,
            ft.Divider(height=20),
            ft.ListTile(
                title=ft.Text("Total a Pagar:", weight=ft.FontWeight.BOLD),
                trailing=ft.Text(f"${total:.2f}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
            ),
            ft.FilledButton(
                content=ft.Text("Confirmar Pedido"), icon="check_circle_outline",
                on_click=confirmar_pedido, width=float('inf')
            )
        ],
        scroll=ft.ScrollMode.ADAPTIVE, spacing=15, expand=True,
    )
