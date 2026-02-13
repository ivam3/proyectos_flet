import flet as ft
import os
import uuid
import shutil
import json
import httpx
from database import (
    obtener_menu,
    agregar_platillo,
    actualizar_platillo,
    eliminar_platillo,
    actualizar_visibilidad_platillo,
    ocultar_todos_los_platillos,
    mostrar_todos_los_platillos,
    get_grupos_opciones,
    subir_imagen
)
from components.notifier import show_notification

def menu_admin_view(page: ft.Page, file_picker: ft.FilePicker):
    
    lista = ft.Column(scroll="auto", expand=True)
    
    upload_status = ft.Text("", color=ft.Colors.BLACK, size=12)
    imagen_path_guardado = ft.Text(visible=False) 

    # --- CAMPOS DE EDICIÓN ---
    nombre_field = ft.TextField(label="Nombre del platillo", text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    descripcion_field = ft.TextField(label="Descripción", multiline=True, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    
    precio_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER, prefix=ft.Text("$", color=ft.Colors.BLACK), text_style=ft.TextStyle(color=ft.Colors.BLACK))
    descuento_field = ft.TextField(label="Descuento %", keyboard_type=ft.KeyboardType.NUMBER, value="0", text_style=ft.TextStyle(color=ft.Colors.BLACK))
    piezas_field = ft.TextField(label="Piezas por orden", keyboard_type=ft.KeyboardType.NUMBER, value="1", text_style=ft.TextStyle(color=ft.Colors.BLACK))

    printer_target_dd = ft.Dropdown(
        label="Área de Preparación",
        options=[
            ft.dropdown.Option("cocina", "Cocina (Interior)"),
            ft.dropdown.Option("foodtruck", "Foodtruck (Exterior)"),
        ],
        value="cocina",
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
    )

    def sync_checkbox_color(chk: ft.Checkbox):
        chk.fill_color = ft.Colors.BROWN_700 if chk.value else ft.Colors.WHITE
    
    def config_chk(tipo): 
        is_config_chk = ft.Checkbox(
            label=f"Configurable ({tipo})",
            value=True,
            label_style=ft.TextStyle(color=ft.Colors.BLACK),
            fill_color=ft.Colors.BROWN_700,
            check_color=ft.Colors.WHITE,
            on_change=lambda e: (sync_checkbox_color(e.control), page.update())
        )
        return is_config_chk

    is_config_chk = config_chk("Guisos")
    is_config_salsa_chk = config_chk("Salsas")
    
    # --- GRUPOS DE OPCIONES DINÁMICOS ---
    grupos_opciones_container = ft.Column()
    grupos_opciones_checks = {} 

    def cargar_checkboxes_grupos():
        grupos_opciones_container.controls.clear()
        grupos_opciones_checks.clear()
        grupos = get_grupos_opciones()
        
        if not grupos:
            grupos_opciones_container.controls.append(ft.Text("No hay grupos extras configurados (Ir a Configuración)", size=12, color=ft.Colors.GREY))
            return

        for g in grupos:
            chk = ft.Checkbox(
                label=f"Opciones: {g['nombre']}",
                value=False,
                label_style=ft.TextStyle(color=ft.Colors.BLACK),
                fill_color=ft.Colors.BROWN_700,
                check_color=ft.Colors.WHITE,
                on_change=lambda e: (sync_checkbox_color(e.control), page.update())
            )
            grupos_opciones_checks[g['id']] = chk
            grupos_opciones_container.controls.append(chk)

    imagen_preview = ft.Image(src="/icon.png", width=80, height=80, fit="cover", visible=False, border_radius=10)
    btn_subir_imagen = ft.FilledButton("Imagen", icon=ft.Icons.IMAGE, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE))

    edit_mode_id = ft.Text(visible=False)

    def limpiar_campos():
        nombre_field.value = ""
        descripcion_field.value = ""
        precio_field.value = ""
        descuento_field.value = "0"
        piezas_field.value = "1"
        printer_target_dd.value = "cocina"
        is_config_chk.value = False
        is_config_salsa_chk.value = False
        
        for chk in grupos_opciones_checks.values():
            chk.value = False
            sync_checkbox_color(chk)
            
        imagen_path_guardado.value = ""
        imagen_preview.src = "/icon.png"
        imagen_preview.visible = False
        edit_mode_id.value = ""
        upload_status.value = ""
        
        btn_accion.text = "Guardar"
        btn_accion.icon = ft.Icons.SAVE
        btn_accion.on_click = agregar_click
        page.update()

    def llenar_campos(platillo):
        pid = platillo['id']
        nom = platillo['nombre']
        desc = platillo.get('descripcion', "")
        pre = platillo['precio']
        img = platillo.get('imagen')
        desc_val = platillo.get('descuento', 0)
        is_conf = platillo.get('is_configurable', 0)
        is_conf_salsa = platillo.get('is_configurable_salsa', 0)
        piezas = platillo.get('piezas', 1)
        printer_target = platillo.get('printer_target', 'cocina')
        grupos_ids_json = platillo.get('grupos_opciones_ids', "[]")

        nombre_field.value = nom
        descripcion_field.value = desc
        precio_field.value = str(pre)
        descuento_field.value = str(desc_val)
        piezas_field.value = str(piezas)
        printer_target_dd.value = printer_target
        is_config_chk.value = bool(is_conf)
        is_config_salsa_chk.value = bool(is_conf_salsa)
        
        try:
            active_ids = json.loads(grupos_ids_json)
            for gid, chk in grupos_opciones_checks.items():
                chk.value = gid in active_ids
                sync_checkbox_color(chk)
        except:
            pass
        
        imagen_path_guardado.value = img
        if img:
            # En producción, las imagenes se sirven desde el backend
            from config import API_URL
            imagen_preview.src = f"{API_URL}/static/uploads/{img}?v={uuid.uuid4()}" 
            imagen_preview.visible = True
        else:
            imagen_preview.src = "/icon.png"
            imagen_preview.visible = False
            
        edit_mode_id.value = str(pid)
        btn_accion.text = "Actualizar"
        btn_accion.icon = ft.Icons.EDIT
        btn_accion.on_click = guardar_cambios_click
        page.update()

    # --- NUEVA LÓGICA DE MANEJO DE ARCHIVOS (HÍBRIDA) ---
    async def process_selected_file(file: ft.FilePickerFile):
        upload_status.value = "Procesando imagen..."
        page.update()
        
        try:
            content = None
            # 1. Intentar obtener bytes directamente (Ideal para Web/Pyodide)
            if hasattr(file, "bytes") and file.bytes:
                print("DEBUG: Usando bytes directos del archivo (Modo Web).")
                content = file.bytes
            
            # 2. Si no hay bytes pero hay path (Modo Local/Android)
            elif file.path:
                print(f"DEBUG: Modo Local detectado: {file.path}")
                with open(file.path, "rb") as f:
                    content = f.read()
            
            if content:
                upload_status.value = "Subiendo al servidor..."
                page.update()
                
                filename = subir_imagen(file.name, content)
                
                if filename:
                    imagen_path_guardado.value = filename
                    from config import API_URL
                    # Forzar recarga con timestamp o UUID para evitar caché del navegador
                    imagen_preview.src = f"{API_URL}/static/uploads/{filename}?v={uuid.uuid4()}"
                    imagen_preview.visible = True
                    upload_status.value = "Carga completa"
                else:
                    upload_status.value = "Error: El servidor rechazó la imagen"
            else:
                upload_status.value = "Error: No se pudo leer el contenido del archivo"
            
        except Exception as ex:
            print(f"Error crítico procesando imagen: {ex}")
            upload_status.value = f"Error: {ex}"
        
        page.update()

    # Configurar el callback del picker global para esta vista
    def on_picker_result(e):
        if e.files:
            # Lanzamos la tarea de procesamiento
            import asyncio
            asyncio.create_task(process_selected_file(e.files[0]))

    # IMPORTANTE: Reasignamos el handler al picker global cada vez que cargamos la vista
    file_picker.on_result = on_picker_result
    # Forzar actualización para que el cliente reconozca el nuevo handler
    try:
        file_picker.update()
    except:
        pass

    async def on_pick_files(e):
         print("DEBUG: Intentando abrir selector de archivos...")
         await file_picker.pick_files(
             allow_multiple=False, 
             file_type=ft.FilePickerFileType.IMAGE
         )

    btn_subir_imagen.on_click = on_pick_files

    def agregar_click(e):
        data = validar_datos()
        if data:
            if agregar_platillo(*data):
                limpiar_campos()
                cargar_lista()
                show_notification(page, "Platillo agregado correctamente", ft.Colors.GREEN)
            else:
                show_notification(page, "Error al agregar platillo (Verificar Backend)", ft.Colors.RED)
            page.update()
        else:
             show_notification(page, "Por favor revise los campos (Precio, Piezas)", ft.Colors.RED)
             page.update()

    def guardar_cambios_click(e):
        data = validar_datos()
        if data and edit_mode_id.value:
            actualizar_platillo(int(edit_mode_id.value), *data)
            limpiar_campos()
            cargar_lista()
            show_notification(page, "Actualizado", ft.Colors.GREEN)
            page.update()

    btn_accion = ft.FilledButton("Guardar", icon=ft.Icons.SAVE, on_click=agregar_click, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE))
    btn_cancelar = ft.FilledButton("Cancelar", icon=ft.Icons.CANCEL, on_click=lambda _: limpiar_campos(), style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE))

    # --- LISTA DE PLATILLOS ---
    def cargar_lista(search_term=""):
        lista.controls.clear()
        platillos = obtener_menu(solo_activos=False, search_term=search_term)
        from config import API_URL
        for p in platillos:
            pid = p['id']
            nom = p['nombre']
            desc = p.get('descripcion', "")
            pre = p['precio']
            img = p.get('imagen')
            active = p.get('is_active', 1)
            is_conf = p.get('is_configurable', 0)
            is_conf_salsa = p.get('is_configurable_salsa', 0)
            target = p.get('printer_target', 'cocina')
            target_color = ft.Colors.BLUE_700 if target == "cocina" else ft.Colors.ORANGE_700
            target_label = "COCINA (INT)" if target == "cocina" else "FOODTRUCK (EXT)"

            extras = []
            if is_conf: extras.append("Guisos")
            if is_conf_salsa: extras.append("Salsas")
            
            desc_final = f"{desc or ''}"
            config_labels = f"({', '.join(extras)})" if extras else ""

            # Imagen del item
            item_img_src = f"{API_URL}/static/uploads/{img}" if img else "/icon.png"

            item_row = ft.Container(
                padding=10,
                bgcolor=ft.Colors.ORANGE_50,
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
                content=ft.Row([
                    ft.Image(src=item_img_src, width=70, height=70, fit="cover", border_radius=8),
                    ft.Column([
                        ft.Row([
                            ft.Text(nom, weight="bold", size=16, color=ft.Colors.BLACK, expand=True),
                            ft.Container(
                                content=ft.Text(target_label, size=10, color=ft.Colors.WHITE, weight="bold"),
                                bgcolor=target_color,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                border_radius=5
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(desc_final, size=13, color=ft.Colors.GREY_800),
                        ft.Text(config_labels, size=11, color=ft.Colors.BROWN_400, italic=True) if config_labels else ft.Container(),
                        ft.Text(f"${pre:.2f}", weight="bold", size=15, color=ft.Colors.BROWN_700),
                        ft.Row([
                            ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BROWN_700, icon_size=20, tooltip="Editar", on_click=lambda e, pl=p: llenar_campos(pl)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=20, tooltip="Eliminar", on_click=lambda e, id=pid: [eliminar_platillo(id), cargar_lista()]),
                            ft.Switch(value=bool(active), scale=0.8, active_color=ft.Colors.GREEN, on_change=lambda e, id=pid: [actualizar_visibilidad_platillo(id, 1 if e.control.value else 0)]),
                        ], spacing=10, alignment=ft.MainAxisAlignment.START)
                    ], expand=True, spacing=2)
                ], vertical_alignment=ft.CrossAxisAlignment.START)
            )
            lista.controls.append(item_row)
        page.update()

    def validar_datos():
        if not nombre_field.value:
            nombre_field.error_text = "Requerido"
            page.update()
            return None
        try:
            p = float(precio_field.value)
        except ValueError:
            precio_field.error_text = "Debe ser número"
            page.update()
            return None
            
        try:
            d = float(descuento_field.value)
        except ValueError:
             descuento_field.value = "0"
             d = 0.0

        try:
            pz = int(piezas_field.value)
        except ValueError:
            piezas_field.error_text = "Entero requerido"
            page.update()
            return None
        
        selected_groups = [gid for gid, chk in grupos_opciones_checks.items() if chk.value]
        grupos_json = json.dumps(selected_groups)
        
        return nombre_field.value, descripcion_field.value, p, imagen_path_guardado.value, d, int(is_config_chk.value), int(is_config_salsa_chk.value), pz, grupos_json, printer_target_dd.value

    search_bar = ft.TextField(
        hint_text="Buscar platillo...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=20, height=40,
        text_size=14, content_padding=10, filled=True,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        on_change=lambda e: cargar_lista(e.control.value)
    )

    global_confirm_dialog = ft.AlertDialog(title=ft.Text("Confirmación"))
    page.overlay.append(global_confirm_dialog)

    def confirmar_accion_global(es_mostrar):
        accion_texto = "MOSTRAR" if es_mostrar else "OCULTAR"
        
        def ejecutar_accion(e):
            if es_mostrar:
                mostrar_todos_los_platillos()
            else:
                ocultar_todos_los_platillos()
            
            cargar_lista()
            global_confirm_dialog.open = False
            show_notification(page, f"Acción '{accion_texto}' completada.", ft.Colors.GREEN)
            page.update()

        global_confirm_dialog.content = ft.Text(f"¿Estás seguro de {accion_texto} todos los platillos?", color=ft.Colors.BLACK)
        global_confirm_dialog.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: setattr(global_confirm_dialog, 'open', False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.GREY)),
            ft.FilledButton("Confirmar", on_click=ejecutar_accion, style=ft.ButtonStyle(bgcolor=ft.Colors.RED if not es_mostrar else ft.Colors.GREEN, color=ft.Colors.WHITE))
        ]
        global_confirm_dialog.open = True
        page.update()

    cargar_lista()
    cargar_checkboxes_grupos() 

    content_container = ft.Container(
        padding=20,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=15,
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Gestión de Menú", size=20, weight="bold", color=ft.Colors.BLACK),
                ft.Divider(),
                nombre_field,
                descripcion_field,
                precio_field,
                descuento_field,
                piezas_field,
                printer_target_dd,
                ft.Column([is_config_chk, is_config_salsa_chk], spacing=0),
                ft.Text("Opciones Extras (Configurado en Ajustes):", size=14, weight="bold", color=ft.Colors.BLACK),
                grupos_opciones_container,
                ft.Divider(),
                ft.Row([btn_subir_imagen, imagen_preview, upload_status], alignment="start", spacing=10),
                ft.Row([btn_accion, btn_cancelar], alignment=ft.MainAxisAlignment.START, spacing=10),
                ft.Divider(),
                search_bar,
                ft.Row([
                    ft.FilledButton("Mostrar Todo", icon=ft.Icons.VISIBILITY, on_click=lambda _: confirmar_accion_global(True), style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE), expand=True),
                    ft.FilledButton("Ocultar Todo", icon=ft.Icons.VISIBILITY_OFF, on_click=lambda _: confirmar_accion_global(False), style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE), expand=True),
                ], spacing=10),
                lista
            ],
            scroll="auto",
            expand=True,
            spacing=15
        )
    )

    return content_container
