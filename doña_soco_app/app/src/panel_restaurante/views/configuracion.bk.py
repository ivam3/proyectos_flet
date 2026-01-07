import flet as ft
import json
from database import get_configuracion, update_configuracion, cambiar_admin_password

def configuracion_view(page: ft.Page):
    # --- Controles de la UI ---
    horario_field = ft.TextField(label="Horario de Atención", border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    codigos_postales_field = ft.TextField(
        label="Códigos Postales Permitidos",
        hint_text="Separados por comas, ej: 12345,54321",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    # --- Configuración de Pagos ---
    pago_efectivo_chk = ft.Checkbox(label="Efectivo", value=True, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
    pago_terminal_chk = ft.Checkbox(label="Terminal", value=True, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
    
    tarjeta_visa_chk = ft.Checkbox(label="Visa", value=True, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
    tarjeta_master_chk = ft.Checkbox(label="Mastercard", value=True, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
    tarjeta_amex_chk = ft.Checkbox(label="Amex", value=False, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
    
    tarjetas_container = ft.Column(
        [
            ft.Text("Tipos de tarjetas aceptadas:", size=14, color=ft.Colors.BLACK),
            ft.Row([tarjeta_visa_chk, tarjeta_master_chk, tarjeta_amex_chk])
        ],
        visible=True
    )

    def on_terminal_change(e):
        tarjetas_container.visible = pago_terminal_chk.value
        page.update()

    pago_terminal_chk.on_change = on_terminal_change

    # --- Configuración de Contacto ---
    telefono_field = ft.TextField(label="Teléfono", border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    email_field = ft.TextField(label="Email", border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    whatsapp_field = ft.TextField(label="Whatsapp", border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    direccion_field = ft.TextField(label="Dirección del Negocio", border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))

    # --- Configuración de Guisos ---
    label_guisos = ft.Text("Guisos Disponibles", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
    guisos_chk = {}
    guisos_list_col = ft.Column()

    # --- Configuración de Salsas ---
    label_salsas = ft.Text("Salsas Disponibles", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
    salsas_chk = {}
    salsas_list_col = ft.Column()

    # --- Cambio de Contraseña Admin ---
    new_password_field = ft.TextField(label="Nueva Contraseña Admin", password=True, can_reveal_password=True, border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    confirm_password_field = ft.TextField(label="Confirmar Contraseña", password=True, can_reveal_password=True, border_radius=10, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))

    def mostrar_notificacion(mensaje, color):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=4000
        )
        page.snack_bar.open = True
        page.update()

    def cargar_datos():
        config = get_configuracion()
        if config:
            horario_field.value = config['horario']
            codigos_postales_field.value = config['codigos_postales']
            
            if config['metodos_pago_activos']:
                try:
                    pagos = json.loads(config['metodos_pago_activos'])
                    pago_efectivo_chk.value = pagos.get('efectivo', True)
                    pago_terminal_chk.value = pagos.get('terminal', True)
                    tarjetas_container.visible = pago_terminal_chk.value
                except: pass

            if config['tipos_tarjeta']:
                try:
                    tarjetas = json.loads(config['tipos_tarjeta'])
                    tarjeta_visa_chk.value = "Visa" in tarjetas
                    tarjeta_master_chk.value = "Mastercard" in tarjetas
                    tarjeta_amex_chk.value = "Amex" in tarjetas
                except: pass

            if config['contactos']:
                try:
                    contactos = json.loads(config['contactos'])
                    telefono_field.value = contactos.get('telefono', "")
                    email_field.value = contactos.get('email', "")
                    whatsapp_field.value = contactos.get('whatsapp', "")
                    direccion_field.value = contactos.get('direccion', "")
                except: pass

            guisos_list_col.controls.clear()
            guisos_chk.clear()
            if config['guisos_disponibles']:
                try:
                    guisos_map = json.loads(config['guisos_disponibles'])
                    for g_nombre, g_activo in guisos_map.items():
                        chk = ft.Checkbox(label=g_nombre, value=g_activo, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
                        guisos_chk[g_nombre] = chk
                        guisos_list_col.controls.append(chk)
                except: pass
            
            salsas_list_col.controls.clear()
            salsas_chk.clear()
            if config['salsas_disponibles']:
                try:
                    salsas_map = json.loads(config['salsas_disponibles'])
                    for s_nombre, s_activo in salsas_map.items():
                        chk = ft.Checkbox(label=s_nombre, value=s_activo, label_style=ft.TextStyle(color=ft.Colors.BLACK), fill_color=ft.Colors.BROWN_700, check_color=ft.Colors.WHITE)
                        salsas_chk[s_nombre] = chk
                        salsas_list_col.controls.append(chk)
                except: pass
        page.update()

    def guardar_click(e):
        pagos_json = json.dumps({"efectivo": pago_efectivo_chk.value, "terminal": pago_terminal_chk.value})
        tarjetas_list = []
        if tarjeta_visa_chk.value: tarjetas_list.append("Visa")
        if tarjeta_master_chk.value: tarjetas_list.append("Mastercard")
        if tarjeta_amex_chk.value: tarjetas_list.append("Amex")
        tarjetas_json = json.dumps(tarjetas_list)
        contactos_json = json.dumps({
            "telefono": telefono_field.value.strip(),
            "email": email_field.value.strip(),
            "whatsapp": whatsapp_field.value.strip(),
            "direccion": direccion_field.value.strip()
        })
        guisos_json = json.dumps({name: chk.value for name, chk in guisos_chk.items()})
        salsas_json = json.dumps({name: chk.value for name, chk in salsas_chk.items()})

        if update_configuracion(horario_field.value, codigos_postales_field.value, pagos_json, tarjetas_json, contactos_json, guisos_json, salsas_json):
            mostrar_notificacion("Configuración guardada correctamente", ft.Colors.GREEN_700)
        else:
            mostrar_notificacion("Error al guardar configuración", ft.Colors.RED)

    def cambiar_pass_click(e):
        p1 = new_password_field.value.strip()
        p2 = confirm_password_field.value.strip()
        if not p1 or not p2:
            mostrar_notificacion("Complete ambos campos de contraseña", ft.Colors.RED)
            return
        if p1 != p2:
            mostrar_notificacion("Las contraseñas no coinciden", ft.Colors.RED)
            return
        if cambiar_admin_password(p1):
             mostrar_notificacion("Contraseña actualizada", ft.Colors.GREEN_700)
             new_password_field.value = ""
             confirm_password_field.value = ""
             page.update()
        else:
             mostrar_notificacion("Error al cambiar contraseña", ft.Colors.RED)

    # Botones con estilo del archivo de referencia
    guardar_button = ft.FilledButton(
        content=ft.Text("Guardar Configuración"),
        on_click=guardar_click,
        icon=ft.Icons.SAVE_OUTLINED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BROWN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15
        )
    )

    cambiar_pass_button = ft.FilledButton(
        content=ft.Text("Actualizar Contraseña"),
        on_click=cambiar_pass_click,
        icon=ft.Icons.LOCK_RESET,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BROWN_700,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15
        )
    )

    cargar_datos()

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Configuración de la Plataforma", size=20, weight="bold", color=ft.Colors.BLACK),
                ft.Divider(),
                horario_field,
                codigos_postales_field,
                ft.Divider(),
                ft.Text("Métodos de Pago", weight="bold", color=ft.Colors.BLACK),
                ft.Row([pago_efectivo_chk, pago_terminal_chk]),
                tarjetas_container,
                ft.Divider(),
                ft.Text("Información de Contacto", weight="bold", color=ft.Colors.BLACK),
                telefono_field, email_field, whatsapp_field, direccion_field,
                ft.Divider(),
                label_guisos, guisos_list_col,
                ft.Divider(),
                label_salsas, salsas_list_col,
                ft.Divider(),
                ft.Container(height=10),
                guardar_button,
                ft.Divider(),
                ft.Text("Seguridad", weight="bold", color=ft.Colors.BLACK),
                ft.Text("Cambiar contraseña de administrador", size=14, color=ft.Colors.GREY_700),
                new_password_field,
                confirm_password_field,
                ft.Container(height=10),
                cambiar_pass_button
            ],
            scroll="auto",
            expand=True,
        ),
        padding=20,
        expand=True
    )