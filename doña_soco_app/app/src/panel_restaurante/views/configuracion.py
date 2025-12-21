import flet as ft
import json
from database import get_configuracion, update_configuracion, cambiar_admin_password

def configuracion_view(page: ft.Page):
    # --- Controles de la UI ---
    horario_field = ft.TextField(label="Horario de Atención", border_radius=10)
    codigos_postales_field = ft.TextField(
        label="Códigos Postales Permitidos",
        hint_text="Separados por comas, ej: 12345,54321",
        border_radius=10
    )

    # --- Configuración de Pagos ---
    pago_efectivo_chk = ft.Checkbox(label="Efectivo", value=True)
    pago_terminal_chk = ft.Checkbox(label="Terminal", value=True)
    
    tarjeta_visa_chk = ft.Checkbox(label="Visa", value=True)
    tarjeta_master_chk = ft.Checkbox(label="Mastercard", value=True)
    tarjeta_amex_chk = ft.Checkbox(label="Amex", value=False)
    
    tarjetas_container = ft.Column(
        [
            ft.Text("Tipos de tarjetas aceptadas:", size=14),
            ft.Row([tarjeta_visa_chk, tarjeta_master_chk, tarjeta_amex_chk])
        ],
        visible=True
    )

    def on_terminal_change(e):
        tarjetas_container.visible = pago_terminal_chk.value
        page.update()

    pago_terminal_chk.on_change = on_terminal_change

    # --- Configuración de Contacto ---
    telefono_field = ft.TextField(label="Teléfono", border_radius=10)
    email_field = ft.TextField(label="Email", border_radius=10)
    whatsapp_field = ft.TextField(label="Whatsapp", border_radius=10)
    direccion_field = ft.TextField(label="Dirección del Negocio", border_radius=10)

    # --- Configuración de Guisos ---
    ft.Text("Guisos Disponibles", size=18, weight=ft.FontWeight.BOLD)
    
    # Diccionarios dinámicos para controles
    guisos_chk = {}
    
    # Contenedor para la lista de guisos
    guisos_list_col = ft.Column()

    guisos_container = ft.Column(
        [
            ft.Text("Gestionar Disponibilidad de Guisos:", size=14),
            guisos_list_col
        ]
    )

    # --- Configuración de Salsas ---
    ft.Text("Salsas Disponibles", size=18, weight=ft.FontWeight.BOLD)
    
    # Diccionarios dinámicos para controles
    salsas_chk = {}

    # Contenedor para la lista de salsas
    salsas_list_col = ft.Column()

    salsas_container = ft.Column(
        [
            ft.Text("Gestionar Disponibilidad de Salsas:", size=14),
            salsas_list_col
        ]
    )

    # --- Controles de Cambio de Password ---
    new_password_field = ft.TextField(label="Nueva Contraseña", password=True, can_reveal_password=True, border_radius=10)
    confirm_password_field = ft.TextField(label="Confirmar Contraseña", password=True, can_reveal_password=True, border_radius=10)

    def mostrar_notificacion(mensaje, color):
        """Muestra un SnackBar con un mensaje."""
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=color,
            duration=4000
        )
        page.snack_bar.open = True
        page.update()

    def guardar_cambios(e):
        """Guarda los nuevos valores en la base de datos y muestra una notificación."""
        horario = horario_field.value.strip()
        codigos = codigos_postales_field.value.strip()
        
        if not horario or not codigos:
            mostrar_notificacion("Horario y códigos postales son obligatorios.", ft.Colors.ERROR)
            return

        # Prepare JSON data
        metodos_pago = json.dumps({
            "efectivo": pago_efectivo_chk.value,
            "terminal": pago_terminal_chk.value
        })
        
        tipos_tarjeta_list = []
        if tarjeta_visa_chk.value: tipos_tarjeta_list.append("Visa")
        if tarjeta_master_chk.value: tipos_tarjeta_list.append("Mastercard")
        if tarjeta_amex_chk.value: tipos_tarjeta_list.append("Amex")
        tipos_tarjeta = json.dumps(tipos_tarjeta_list)
        
        contactos = json.dumps({
            "telefono": telefono_field.value.strip(),
            "email": email_field.value.strip(),
            "whatsapp": whatsapp_field.value.strip(),
            "direccion": direccion_field.value.strip()
        })

        guisos_disponibles = json.dumps({k: v.value for k, v in guisos_chk.items()})
        salsas_disponibles = json.dumps({k: v.value for k, v in salsas_chk.items()})

        if update_configuracion(horario, codigos, metodos_pago, tipos_tarjeta, contactos, guisos_disponibles, salsas_disponibles):
            mostrar_notificacion("Configuración guardada exitosamente.", ft.Colors.GREEN_700)
        else:
            mostrar_notificacion("Error al guardar la configuración.", ft.Colors.ERROR)

    def cambiar_password(e):
        p1 = new_password_field.value
        p2 = confirm_password_field.value

        if not p1 or not p2:
            mostrar_notificacion("Ingresa la nueva contraseña en ambos campos.", ft.Colors.ERROR)
            return
        
        if p1 != p2:
            mostrar_notificacion("Las contraseñas no coinciden.", ft.Colors.ERROR)
            return

        if cambiar_admin_password(p1):
            # Popup de confirmación
            dlg = ft.AlertDialog(
                title=ft.Text("Cambio de Contraseña Exitoso"),
                content=ft.Text("La contraseña de administrador ha sido actualizada correctamente."),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda e: setattr(dlg, "open", False) or page.update())
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            
            new_password_field.value = ""
            confirm_password_field.value = ""
            page.update()
        else:
            mostrar_notificacion("Error al actualizar la contraseña.", ft.Colors.ERROR)

    def cargar_datos_actuales():
        """Carga la configuración actual desde la base de datos y la muestra en los campos."""
        config = get_configuracion()
        if config:
            horario_field.value = config['horario']
            codigos_postales_field.value = config['codigos_postales']
            
            # Cargar métodos de pago
            if 'metodos_pago_activos' in config.keys() and config['metodos_pago_activos']:
                try:
                    pagos = json.loads(config['metodos_pago_activos'])
                    pago_efectivo_chk.value = pagos.get("efectivo", True)
                    pago_terminal_chk.value = pagos.get("terminal", True)
                    tarjetas_container.visible = pago_terminal_chk.value
                except json.JSONDecodeError:
                    pass
            
            # Cargar tipos de tarjeta
            if 'tipos_tarjeta' in config.keys() and config['tipos_tarjeta']:
                try:
                    tarjetas = json.loads(config['tipos_tarjeta'])
                    tarjeta_visa_chk.value = "Visa" in tarjetas
                    tarjeta_master_chk.value = "Mastercard" in tarjetas
                    tarjeta_amex_chk.value = "Amex" in tarjetas
                except json.JSONDecodeError:
                    pass
            
            # Cargar contactos
            if 'contactos' in config.keys() and config['contactos']:
                try:
                    contactos = json.loads(config['contactos'])
                    telefono_field.value = contactos.get("telefono", "")
                    email_field.value = contactos.get("email", "")
                    whatsapp_field.value = contactos.get("whatsapp", "")
                    direccion_field.value = contactos.get("direccion", "")
                except json.JSONDecodeError:
                    pass

            # --- Cargar guisos dinámicamente ---
            guisos_data = {}
            # Defaults históricos para asegurar consistencia si la BD está vacía o incompleta
            defaults_guisos = ["Deshebrada", "Nopalitos", "Queso", "Picadillo", "Chicharrón"]
            
            if 'guisos_disponibles' in config.keys() and config['guisos_disponibles']:
                try:
                    guisos_data = json.loads(config['guisos_disponibles'])
                except json.JSONDecodeError:
                    pass
            
            # Asegurar que los defaults estén presentes
            for d in defaults_guisos:
                if d not in guisos_data:
                    guisos_data[d] = True

            # Reconstruir UI de guisos
            guisos_chk.clear()
            guisos_list_col.controls.clear()
            for nombre, activo in guisos_data.items():
                chk = ft.Checkbox(label=nombre, value=activo)
                guisos_chk[nombre] = chk
                guisos_list_col.controls.append(chk)


            # --- Cargar salsas dinámicamente ---
            salsas_data = {}
            defaults_salsas = ["BBQ", "Búfalo", "Chipotle", "Habanero", "Mango Habanero", "BBQ Hot", "Piquín Limón"]

            if 'salsas_disponibles' in config.keys() and config['salsas_disponibles']:
                try:
                    salsas_data = json.loads(config['salsas_disponibles'])
                except json.JSONDecodeError:
                    pass
            
            for d in defaults_salsas:
                if d not in salsas_data:
                    salsas_data[d] = True

            # Reconstruir UI de salsas
            salsas_chk.clear()
            salsas_list_col.controls.clear()
            for nombre, activo in salsas_data.items():
                chk = ft.Checkbox(label=nombre, value=activo)
                salsas_chk[nombre] = chk
                salsas_list_col.controls.append(chk)

            page.update()

    guardar_button = ft.Button(
        content=ft.Text("Guardar Configuración"),
        on_click=guardar_cambios,
        icon=ft.Icons.SAVE_OUTLINED,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15
        )
    )

    cambiar_pass_button = ft.Button(
        content=ft.Text("Actualizar Contraseña"),
        on_click=cambiar_password,
        icon=ft.Icons.LOCK_RESET,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.ORANGE_700,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15
        )
    )

    content_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Configuración de la Plataforma", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                horario_field,
                codigos_postales_field,
                
                ft.Divider(height=20),
                ft.Text("Métodos de Pago", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([pago_efectivo_chk, pago_terminal_chk]),
                tarjetas_container,
                
                ft.Divider(height=20),
                ft.Text("Guisos Disponibles", size=18, weight=ft.FontWeight.BOLD),
                guisos_container,

                ft.Divider(height=20),
                ft.Text("Salsas Disponibles", size=18, weight=ft.FontWeight.BOLD),
                salsas_container,

                ft.Divider(height=20),
                ft.Text("Información de Contacto", size=18, weight=ft.FontWeight.BOLD),
                telefono_field,
                email_field,
                whatsapp_field,
                direccion_field,
                
                ft.Container(height=10), # Espaciador
                guardar_button,
                
                ft.Divider(height=30),
                
                ft.Text("Seguridad", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Cambiar contraseña de administrador", size=14, color=ft.Colors.GREY_700),
                new_password_field,
                confirm_password_field,
                ft.Container(height=10),
                cambiar_pass_button
            ],
            spacing=15,
        ),
        padding=20,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=15,
    )

    cargar_datos_actuales()

    return ft.Column([content_container], scroll="auto")