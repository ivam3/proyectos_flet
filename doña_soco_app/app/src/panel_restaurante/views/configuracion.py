import flet as ft
import json
from database import (
    get_configuracion,
    update_configuracion,
    cambiar_admin_password,
    get_grupos_opciones,
    create_grupo_opciones,
    delete_grupo_opciones
)


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
    
    nuevo_guiso_input = ft.TextField(hint_text="Nuevo Guiso (ej: Chicharrón)", text_style=ft.TextStyle(color=ft.Colors.BLACK), hint_style=ft.TextStyle(color=ft.Colors.GREY), expand=True)
    
    def agregar_guiso_action(e):
        nombre = nuevo_guiso_input.value.strip()
        if nombre and nombre not in guisos_chk:
            crear_item_row(nombre, True, guisos_chk, guisos_list_col)
            nuevo_guiso_input.value = ""
            page.update()
        else:
            if nombre in guisos_chk:
                mostrar_notificacion("Ese guiso ya existe", ft.Colors.ORANGE)
            else:
                mostrar_notificacion("Escribe un nombre", ft.Colors.RED)

    btn_add_guiso = ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN, on_click=agregar_guiso_action)

    # --- Configuración de Salsas ---
    label_salsas = ft.Text(
        "Salsas Disponibles",
        size=18,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
    )

    salsas_chk = {}
    salsas_list_col = ft.Column()
    
    nueva_salsa_input = ft.TextField(hint_text="Nueva Salsa (ej: Verde)", text_style=ft.TextStyle(color=ft.Colors.BLACK), hint_style=ft.TextStyle(color=ft.Colors.GREY), expand=True)

    def agregar_salsa_action(e):
        nombre = nueva_salsa_input.value.strip()
        if nombre and nombre not in salsas_chk:
            crear_item_row(nombre, True, salsas_chk, salsas_list_col)
            nueva_salsa_input.value = ""
            page.update()
        else:
            if nombre in salsas_chk:
                mostrar_notificacion("Esa salsa ya existe", ft.Colors.ORANGE)
            else:
                mostrar_notificacion("Escribe un nombre", ft.Colors.RED)

    btn_add_salsa = ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN, on_click=agregar_salsa_action)

    def crear_item_row(name, val, target_dict, target_col):
        chk = ft.Checkbox(
            label=name,
            value=val,
            label_style=ft.TextStyle(color=ft.Colors.BLACK),
            fill_color=ft.Colors.BROWN_700 if val else ft.Colors.WHITE,
            check_color=ft.Colors.WHITE,
            on_change=lambda e: (sync_checkbox_color(e.control), page.update()),
        )
        # Guardamos referencia para el guardado final
        target_dict[name] = chk
        
        def delete_item(e):
            del target_dict[name]
            target_col.controls.remove(row)
            page.update()

        row = ft.Row([
            chk,
            ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=delete_item, tooltip="Eliminar")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        target_col.controls.append(row)
        return row

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
    
    # --- GESTIÓN DE GRUPOS DE OPCIONES (NUEVO) ---
    nombre_grupo_field = ft.TextField(label="Nombre del Grupo (ej: Termino)", border_radius=10, expand=True, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    opciones_grupo_field = ft.TextField(label="Opciones (separadas por coma)", hint_text="Ej: Dorado, Suave, Medio", border_radius=10, expand=True, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    
    lista_grupos_col = ft.Column(spacing=10)

    def cargar_grupos_opciones():
        lista_grupos_col.controls.clear()
        grupos = get_grupos_opciones()
        
        for g in grupos:
            # g: id, nombre, opciones (str json), ...
            try:
                ops = json.loads(g['opciones'])
                ops_str = ", ".join(ops)
            except:
                ops_str = g['opciones']

            item = ft.Container(
                padding=10,
                bgcolor=ft.Colors.GREY_100,
                border_radius=8,
                content=ft.Row([
                    ft.Column([
                        ft.Text(g['nombre'], weight="bold", color=ft.Colors.BLACK),
                        ft.Text(ops_str, size=12, color=ft.Colors.GREY_700),
                    ], expand=True),
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, gid=g['id']: borrar_grupo_click(gid))
                ])
            )
            lista_grupos_col.controls.append(item)
        page.update()

    def agregar_grupo_click(e):
        if not nombre_grupo_field.value or not opciones_grupo_field.value:
            mostrar_notificacion("Complete todos los campos del grupo", ft.Colors.RED)
            return
            
        # Convertir CSV a JSON List
        ops_list = [x.strip() for x in opciones_grupo_field.value.split(",") if x.strip()]
        ops_json = json.dumps(ops_list)
        
        if create_grupo_opciones(nombre_grupo_field.value, ops_json):
            mostrar_notificacion("Grupo agregado", ft.Colors.GREEN_700)
            nombre_grupo_field.value = ""
            opciones_grupo_field.value = ""
            cargar_grupos_opciones()
        else:
            mostrar_notificacion("Error al crear grupo", ft.Colors.RED)

    def borrar_grupo_click(gid):
        if delete_grupo_opciones(gid):
            cargar_grupos_opciones()
            mostrar_notificacion("Grupo eliminado", ft.Colors.ORANGE)

    btn_add_grupo = ft.FilledButton("Agregar Grupo", icon=ft.Icons.ADD, on_click=agregar_grupo_click, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE))

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
            crear_item_row(name, val, guisos_chk, guisos_list_col)

        salsas_list_col.controls.clear()
        salsas_chk.clear()

        for name, val in json.loads(config["salsas_disponibles"]).items():
            crear_item_row(name, val, salsas_chk, salsas_list_col)

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
    cargar_grupos_opciones() # Cargar al inicio

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
                ft.Text("Opciones Configurables (Extras)", size=18, weight="bold", color=ft.Colors.BLACK),
                ft.Text("Crea grupos de opciones (ej: Término, Verduras) para asignarlos a los platillos.", size=12, color=ft.Colors.GREY_700),
                ft.Row([nombre_grupo_field, opciones_grupo_field], spacing=10),
                btn_add_grupo,
                lista_grupos_col,
                ft.Divider(),
                label_guisos,
                ft.Row([nuevo_guiso_input, btn_add_guiso]),
                guisos_list_col,
                ft.Divider(),
                label_salsas,
                ft.Row([nueva_salsa_input, btn_add_salsa]),
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
