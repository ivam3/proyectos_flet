import flet as ft
import json
from database import get_configuracion, update_configuracion, cambiar_admin_password


def configuracion_view(page: ft.Page):

    # ---------- FIX VISUAL CHECKBOX (CAMBIO MÍNIMO) ----------
    def sync_checkbox_color(chk: ft.Checkbox):
        chk.fill_color = ft.Colors.BROWN_700 if chk.value else ft.Colors.WHITE

    # --- Controles de la UI ---
    horario_field = ft.TextField(
        label="Horario de Atención",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    codigos_postales_field = ft.TextField(
        label="Códigos Postales Permitidos",
        hint_text="Separados por comas, ej: 12345,54321",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    # --- Configuración de Pagos ---
    pago_efectivo_chk = ft.Checkbox(
        label="Efectivo",
        value=True,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        fill_color=ft.Colors.BROWN_700,
        check_color=ft.Colors.WHITE,
        on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
    )

    pago_terminal_chk = ft.Checkbox(
        label="Terminal",
        value=True,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        fill_color=ft.Colors.BROWN_700,
        check_color=ft.Colors.WHITE,
        on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
    )

    tarjeta_visa_chk = ft.Checkbox(
        label="Visa",
        value=True,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        fill_color=ft.Colors.BROWN_700,
        check_color=ft.Colors.WHITE,
        on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
    )

    tarjeta_master_chk = ft.Checkbox(
        label="Mastercard",
        value=True,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        fill_color=ft.Colors.BROWN_700,
        check_color=ft.Colors.WHITE,
        on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
    )

    tarjeta_amex_chk = ft.Checkbox(
        label="Amex",
        value=False,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        fill_color=ft.Colors.WHITE,
        check_color=ft.Colors.WHITE,
        on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
    )

    tarjetas_container = ft.Column(
        [
            ft.Text("Tipos de tarjetas aceptadas:", size=14, color=ft.Colors.BLACK),
            ft.Row([tarjeta_visa_chk, tarjeta_master_chk, tarjeta_amex_chk]),
        ],
        visible=True,
    )

    def on_terminal_change(e):
        tarjetas_container.visible = pago_terminal_chk.value
        page.update()

    pago_terminal_chk.on_change = lambda e: (
        sync_checkbox_color(e.control),
        on_terminal_change(e),
    )

    # --- Configuración de Contacto ---
    telefono_field = ft.TextField(
        label="Teléfono",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    email_field = ft.TextField(
        label="Email",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    whatsapp_field = ft.TextField(
        label="Whatsapp",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    direccion_field = ft.TextField(
        label="Dirección del Negocio",
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    # --- Configuración de Guisos ---
    label_guisos = ft.Text(
        "Guisos Disponibles",
        size=18,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
    )

    guisos_chk = {}
    guisos_list_col = ft.Column()

    # --- Configuración de Salsas ---
    label_salsas = ft.Text(
        "Salsas Disponibles",
        size=18,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
    )

    salsas_chk = {}
    salsas_list_col = ft.Column()

    # --- Cambio de Contraseña Admin ---
    new_password_field = ft.TextField(
        label="Nueva Contraseña Admin",
        password=True,
        can_reveal_password=True,
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    confirm_password_field = ft.TextField(
        label="Confirmar Contraseña",
        password=True,
        can_reveal_password=True,
        border_radius=10,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    def mostrar_notificacion(mensaje, color):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=4000,
        )
        page.snack_bar.open = True
        page.update()

    def cargar_datos():
        config = get_configuracion()
        if not config:
            return

        horario_field.value = config["horario"]
        codigos_postales_field.value = config["codigos_postales"]

        pagos = json.loads(config["metodos_pago_activos"])
        pago_efectivo_chk.value = pagos.get("efectivo", True)
        pago_terminal_chk.value = pagos.get("terminal", True)

        for chk in [pago_efectivo_chk, pago_terminal_chk]:
            sync_checkbox_color(chk)

        tarjetas_container.visible = pago_terminal_chk.value

        tarjetas = json.loads(config["tipos_tarjeta"])
        tarjeta_visa_chk.value = "Visa" in tarjetas
        tarjeta_master_chk.value = "Mastercard" in tarjetas
        tarjeta_amex_chk.value = "Amex" in tarjetas

        for chk in [tarjeta_visa_chk, tarjeta_master_chk, tarjeta_amex_chk]:
            sync_checkbox_color(chk)

        contactos = json.loads(config["contactos"])
        telefono_field.value = contactos.get("telefono", "")
        email_field.value = contactos.get("email", "")
        whatsapp_field.value = contactos.get("whatsapp", "")
        direccion_field.value = contactos.get("direccion", "")

        guisos_list_col.controls.clear()
        guisos_chk.clear()

        for name, val in json.loads(config["guisos_disponibles"]).items():
            chk = ft.Checkbox(
                label=name,
                value=val,
                label_style=ft.TextStyle(color=ft.Colors.BLACK),
                fill_color=ft.Colors.BROWN_700 if val else ft.Colors.WHITE,
                check_color=ft.Colors.WHITE,
                on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
            )
            guisos_chk[name] = chk
            guisos_list_col.controls.append(chk)

        salsas_list_col.controls.clear()
        salsas_chk.clear()

        for name, val in json.loads(config["salsas_disponibles"]).items():
            chk = ft.Checkbox(
                label=name,
                value=val,
                label_style=ft.TextStyle(color=ft.Colors.BLACK),
                fill_color=ft.Colors.BROWN_700 if val else ft.Colors.WHITE,
                check_color=ft.Colors.WHITE,
                on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
            )
            salsas_chk[name] = chk
            salsas_list_col.controls.append(chk)

        page.update()

    # --------- RESTO DEL CÓDIGO ORIGINAL (BOTONES INTACTOS) ---------

    def guardar_click(e):
        pagos_json = json.dumps(
            {"efectivo": pago_efectivo_chk.value, "terminal": pago_terminal_chk.value}
        )

        tarjetas = []
        if tarjeta_visa_chk.value:
            tarjetas.append("Visa")
        if tarjeta_master_chk.value:
            tarjetas.append("Mastercard")
        if tarjeta_amex_chk.value:
            tarjetas.append("Amex")

        tarjetas_json = json.dumps(tarjetas)

        contactos_json = json.dumps(
            {
                "telefono": telefono_field.value.strip(),
                "email": email_field.value.strip(),
                "whatsapp": whatsapp_field.value.strip(),
                "direccion": direccion_field.value.strip(),
            }
        )

        guisos_json = json.dumps({k: v.value for k, v in guisos_chk.items()})
        salsas_json = json.dumps({k: v.value for k, v in salsas_chk.items()})

        if update_configuracion(
            horario_field.value,
            codigos_postales_field.value,
            pagos_json,
            tarjetas_json,
            contactos_json,
            guisos_json,
            salsas_json,
        ):
            mostrar_notificacion("Configuración guardada correctamente", ft.Colors.GREEN_700)
        else:
            mostrar_notificacion("Error al guardar configuración", ft.Colors.RED)

    def cambiar_pass_click(e):
        if new_password_field.value != confirm_password_field.value:
            mostrar_notificacion("Las contraseñas no coinciden", ft.Colors.RED)
            return

        if cambiar_admin_password(new_password_field.value):
            mostrar_notificacion("Contraseña actualizada", ft.Colors.GREEN_700)
            new_password_field.value = ""
            confirm_password_field.value = ""
            page.update()

    guardar_button = ft.FilledButton(
        content=ft.Text("Guardar Configuración"),
        on_click=guardar_click,
        icon=ft.Icons.SAVE_OUTLINED,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BROWN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15,
        ),
    )

    cambiar_pass_button = ft.FilledButton(
        content=ft.Text("Actualizar Contraseña"),
        on_click=cambiar_pass_click,
        icon=ft.Icons.LOCK_RESET,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BROWN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15,
        ),
    )

    cargar_datos()

    content_container = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Configuración de la Plataforma",
                    size=20,
                    weight="bold",
                    color=ft.Colors.BLACK,
                ),
                ft.Divider(),
                horario_field,
                codigos_postales_field,
                ft.Divider(),
                ft.Text("Métodos de Pago", weight="bold", color=ft.Colors.BLACK),
                ft.Row([pago_efectivo_chk, pago_terminal_chk]),
                tarjetas_container,
                ft.Divider(),
                ft.Text("Información de Contacto", weight="bold", color=ft.Colors.BLACK),
                telefono_field,
                email_field,
                whatsapp_field,
                direccion_field,
                ft.Divider(),
                label_guisos,
                guisos_list_col,
                ft.Divider(),
                label_salsas,
                salsas_list_col,
                ft.Divider(),
                guardar_button,
                ft.Divider(),
                ft.Text("Seguridad", weight="bold", color=ft.Colors.BLACK),
                new_password_field,
                confirm_password_field,
                cambiar_pass_button,
            ],
            scroll="auto",
            expand=True,
            spacing=15 # Agregado spacing para consistencia
        ),
        padding=20,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=15,
        expand=True,
    )

    return ft.Column([content_container], expand=True)
