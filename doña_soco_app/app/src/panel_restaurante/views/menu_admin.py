import flet as ft
import os
import uuid
import shutil
import json
from database import (
    obtener_menu,
    agregar_platillo,
    actualizar_platillo,
    eliminar_platillo,
    actualizar_visibilidad_platillo,
    ocultar_todos_los_platillos,
    mostrar_todos_los_platillos,
    get_grupos_opciones
)

# Definimos menu_admin_view sin usar el file_picker global
def menu_admin_view(page: ft.Page, file_picker_ignored: ft.FilePicker):
    
    # --- SELECTOR DE ARCHIVOS LOCAL (Estrategia probada en Pedidos) ---
    # Creamos una instancia local del FilePicker para esta vista
    file_picker = ft.FilePicker()

    lista = ft.Column(scroll="auto", expand=True)
    
    upload_status = ft.Text("", color=ft.Colors.BLACK, size=12)
    imagen_path_guardado = ft.Text(visible=False) 

    # --- CAMPOS DE EDICIÓN ---
    nombre_field = ft.TextField(label="Nombre del platillo", text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    descripcion_field = ft.TextField(label="Descripción", multiline=True, text_style=ft.TextStyle(color=ft.Colors.BLACK), label_style=ft.TextStyle(color=ft.Colors.BLACK))
    
    precio_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER, prefix=ft.Text("$", color=ft.Colors.BLACK), text_style=ft.TextStyle(color=ft.Colors.BLACK))
    descuento_field = ft.TextField(label="Descuento %", keyboard_type=ft.KeyboardType.NUMBER, value="0", text_style=ft.TextStyle(color=ft.Colors.BLACK))
    piezas_field = ft.TextField(label="Piezas por orden", keyboard_type=ft.KeyboardType.NUMBER, value="1", text_style=ft.TextStyle(color=ft.Colors.BLACK))

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
    # Contenedor para checkboxes generados dinámicamente
    grupos_opciones_container = ft.Column()
    grupos_opciones_checks = {} # Map id -> checkbox

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
        is_config_chk.value = False
        is_config_salsa_chk.value = False
        
        # Reset dynamic checks
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
        # pid, nom, desc, pre, img, active, desc_val, is_conf, is_conf_salsa, piezas = platillo
        pid = platillo['id']
        nom = platillo['nombre']
        desc = platillo.get('descripcion', "")
        pre = platillo['precio']
        img = platillo.get('imagen')
        desc_val = platillo.get('descuento', 0)
        is_conf = platillo.get('is_configurable', 0)
        is_conf_salsa = platillo.get('is_configurable_salsa', 0)
        piezas = platillo.get('piezas', 1)
        grupos_ids_json = platillo.get('grupos_opciones_ids', "[]")

        nombre_field.value = nom
        descripcion_field.value = desc
        precio_field.value = str(pre)
        descuento_field.value = str(desc_val)
        piezas_field.value = str(piezas)
        is_config_chk.value = bool(is_conf)
        is_config_salsa_chk.value = bool(is_conf_salsa)
        
        # Load dynamic checks
        try:
            active_ids = json.loads(grupos_ids_json)
            for gid, chk in grupos_opciones_checks.items():
                chk.value = gid in active_ids
                sync_checkbox_color(chk)
        except:
            pass
        
        imagen_path_guardado.value = img
        if img:
            imagen_preview.src = f"/{img}?v={uuid.uuid4()}" 
            imagen_preview.visible = True
        else:
            imagen_preview.src = "/icon.png"
            imagen_preview.visible = False
            
        edit_mode_id.value = str(pid)
        btn_accion.text = "Actualizar"
        btn_accion.icon = ft.Icons.EDIT
        btn_accion.on_click = guardar_cambios_click
        page.update()

    # Cálculo de la ruta de assets
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "assets"))

    def on_upload_completed(e: ft.FilePickerUploadEvent):
        print(f"DEBUG: Upload completed for {e.file_name}, error={e.error}")
        if e.error:
            upload_status.value = f"Error upload: {e.error}"
            page.update()
            return

        try:
            source_path = os.path.join(page.upload_dir, e.file_name)
            ext = os.path.splitext(e.file_name)[1]
            nuevo_nombre = f"{uuid.uuid4()}{ext}"
            destino = os.path.join(assets_dir, nuevo_nombre)
            
            print(f"DEBUG: Moviendo de {source_path} a {destino}")
            shutil.move(source_path, destino)
            
            imagen_path_guardado.value = nuevo_nombre
            imagen_preview.src = f"/{nuevo_nombre}?v={uuid.uuid4()}"
            imagen_preview.visible = True
            upload_status.value = "Carga completa"
            print("DEBUG: Imagen procesada tras subida")
        except Exception as ex:
            print(f"DEBUG ERROR post-upload: {ex}")
            upload_status.value = f"Error procesando: {ex}"
        
        page.update()

    # Asignar handlers al picker LOCAL
    file_picker.on_upload = on_upload_completed

    def imagen_seleccionada(e):
        print(f"DEBUG: imagen_seleccionada invocado. Files: {e.files}")
        if e.files:
            file = e.files[0]
            # Si tiene path local (Desktop)
            if file.path:
                try:
                    print(f"DEBUG: Modo Local - Guardando en {assets_dir}")
                    os.makedirs(assets_dir, exist_ok=True)
                    ext = os.path.splitext(file.name)[1]
                    nuevo_nombre = f"{uuid.uuid4()}{ext}"
                    destino = os.path.join(assets_dir, nuevo_nombre)
                    print(f"DEBUG: Copiando de {file.path} a {destino}")
                    shutil.copy(file.path, destino)
                    imagen_path_guardado.value = nuevo_nombre
                    imagen_preview.src = f"/{nuevo_nombre}?v={uuid.uuid4()}" 
                    imagen_preview.visible = True
                    upload_status.value = "Lista"
                    print("DEBUG: Imagen guardada correctamente (Local)")
                except Exception as ex:
                    print(f"DEBUG ERROR: {ex}")
                    upload_status.value = f"Error: {ex}"
                page.update()
            else:
                # Si NO tiene path (Web/Mobile), hay que subirlo
                print("DEBUG: Modo Upload - Iniciando subida...")
                upload_status.value = "Subiendo..."
                page.update()
                try:
                    os.makedirs(page.upload_dir, exist_ok=True)
                    upload_list = [
                        ft.FilePickerUploadFile(
                            file.name,
                            upload_url=page.get_upload_url(file.name, 600)
                        )
                    ]
                    file_picker.upload(upload_list)
                except Exception as ex:
                    print(f"DEBUG ERROR Upload Init: {ex}")
                    upload_status.value = f"Error inicio subida: {ex}"
                    page.update()
        else:
            print("DEBUG: No files selected")

    file_picker.on_result = imagen_seleccionada

    async def on_pick_files(e):
         await file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    btn_subir_imagen.on_click = on_pick_files

    def agregar_click(e):
        data = validar_datos()
        if data:
            if agregar_platillo(*data):
                limpiar_campos()
                cargar_lista()
                page.snack_bar = ft.SnackBar(ft.Text("Platillo agregado correctamente", color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Error al agregar platillo (Verificar Backend)", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
        else:
             page.snack_bar = ft.SnackBar(ft.Text("Por favor revise los campos (Precio, Piezas)", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED)
             page.snack_bar.open = True
             page.update()

    def guardar_cambios_click(e):
        data = validar_datos()
        if data and edit_mode_id.value:
            actualizar_platillo(int(edit_mode_id.value), *data)
            limpiar_campos()
            cargar_lista()
            page.snack_bar = ft.SnackBar(ft.Text("Actualizado"))
            page.snack_bar.open = True
            page.update()

    btn_accion = ft.FilledButton("Guardar", icon=ft.Icons.SAVE, on_click=agregar_click, style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE))
    btn_cancelar = ft.FilledButton("Cancelar", icon=ft.Icons.CANCEL, on_click=lambda _: limpiar_campos(), style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE))

    # --- LISTA DE PLATILLOS ---
    def cargar_lista(search_term=""):
        lista.controls.clear()
        platillos = obtener_menu(solo_activos=False, search_term=search_term)
        for p in platillos:
            # pid, nom, desc, pre, img, active, desc_val, is_conf, is_conf_salsa, piezas = p
            pid = p['id']
            nom = p['nombre']
            desc = p.get('descripcion', "")
            pre = p['precio']
            img = p.get('imagen')
            active = p.get('is_active', 1)
            is_conf = p.get('is_configurable', 0)
            is_conf_salsa = p.get('is_configurable_salsa', 0)

            extras = []
            if is_conf: extras.append("Guisos")
            if is_conf_salsa: extras.append("Salsas")
            desc_final = f"{desc or ''} ({', '.join(extras)})" if extras else (desc or "")

            item_row = ft.Container(
                padding=10,
                bgcolor=ft.Colors.ORANGE_50,
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
                content=ft.Row([
                    ft.Image(src=f"/{img}" if img else "/icon.png", width=60, height=60, fit="cover", border_radius=8),
                    ft.Column([
                        ft.Text(nom, weight="bold", size=14, color=ft.Colors.BLACK),
                        ft.Text(desc_final, size=12, color=ft.Colors.GREY_700, max_lines=2, overflow="ellipsis"),
                        ft.Text(f"${pre:.2f}", weight="bold", color=ft.Colors.BROWN_700),
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
        
        # Collect checked groups
        selected_groups = [gid for gid, chk in grupos_opciones_checks.items() if chk.value]
        grupos_json = json.dumps(selected_groups)
        
        return nombre_field.value, descripcion_field.value, p, imagen_path_guardado.value, d, int(is_config_chk.value), int(is_config_salsa_chk.value), pz, grupos_json

    search_bar = ft.TextField(
        hint_text="Buscar platillo...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=20, height=40,
        text_size=14, content_padding=10, filled=True,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        on_change=lambda e: cargar_lista(e.control.value)
    )

    # --- DIÁLOGO DE CONFIRMACIÓN GLOBAL ---
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
            page.snack_bar = ft.SnackBar(ft.Text(f"Acción '{accion_texto}' completada."))
            page.snack_bar.open = True
            page.update()

        global_confirm_dialog.content = ft.Text(f"¿Estás seguro de {accion_texto} todos los platillos?", color=ft.Colors.BLACK)
        global_confirm_dialog.actions = [
            ft.TextButton("Cancelar", on_click=lambda e: setattr(global_confirm_dialog, 'open', False) or page.update(), style=ft.ButtonStyle(color=ft.Colors.GREY)),
            ft.FilledButton("Confirmar", on_click=ejecutar_accion, style=ft.ButtonStyle(bgcolor=ft.Colors.RED if not es_mostrar else ft.Colors.GREEN, color=ft.Colors.WHITE))
        ]
        global_confirm_dialog.open = True
        page.update()

    cargar_lista()
    cargar_checkboxes_grupos() # Inicializar checks dinámicos

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
                ft.Column([is_config_chk, is_config_salsa_chk], spacing=0),
                ft.Text("Opciones Extras (Configurado en Ajustes):", size=14, weight="bold", color=ft.Colors.BLACK),
                grupos_opciones_container,
                ft.Divider(),
                ft.Row([btn_subir_imagen, imagen_preview, upload_status], alignment="start", spacing=10),
                # BOTONES ALINEADOS A LA IZQUIERDA (START)
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

    # Añadir el FilePicker LOCAL al árbol de controles (invisible pero activo)
    # IMPORTANTE: Esto lo integra en la página y permite que se abra el selector nativo
    return ft.Column([content_container, ft.Container(content=file_picker, width=0, height=0)], expand=True)
