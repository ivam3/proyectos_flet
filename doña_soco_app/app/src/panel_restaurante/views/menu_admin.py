import flet as ft
import os
import uuid
import httpx
import shutil
from database import (
    obtener_menu,
    agregar_platillo,
    actualizar_platillo,
    eliminar_platillo,
    actualizar_visibilidad_platillo,
    ocultar_todos_los_platillos,
    mostrar_todos_los_platillos,
)

def menu_admin_view(page: ft.Page, file_picker: ft.FilePicker):

    # Aumentamos el área de scroll y la definimos como expandible para que ocupe todo el alto posible
    lista = ft.Column(scroll="auto", expand=True)
    
    # Vinculamos el evento de subida al picker global
    def on_upload_progress(e):
        """Maneja la finalización de la subida (Estrategia 2)."""
        if e.error:
            upload_status.value = f"Error en la subida: {e.error}"
        elif e.progress == 1.0: 
            try:
                # Recuperar y guardar
                temp_url = page.get_upload_url(e.file_name)
                response = httpx.get(temp_url)
                response.raise_for_status()

                assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
                os.makedirs(assets_dir, exist_ok=True)
                
                ext = os.path.splitext(e.file_name)[1]
                nuevo_nombre = f"{uuid.uuid4()}{ext}"
                destino = os.path.join(assets_dir, nuevo_nombre)
                
                with open(destino, "wb") as f:
                    f.write(response.content)

                finalizar_guardado(nuevo_nombre)
                
            except Exception as ex:
                upload_status.value = f"Error al guardar desde buffer: {ex}"
        
        page.update()

    file_picker.on_upload = on_upload_progress

    nombre_field = ft.TextField(label="Nombre del platillo")
    descripcion_field = ft.TextField(label="Descripción", multiline=True)
    precio_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER)
    descuento_field = ft.TextField(label="Descuento (%)", keyboard_type=ft.KeyboardType.NUMBER, value="0")
    piezas_field = ft.TextField(label="Piezas por Orden", keyboard_type=ft.KeyboardType.NUMBER, value="1", hint_text="Ej: 3 para orden de 3 gorditas")
    
    is_configurable_chk = ft.Checkbox(label="¿Platillo Configurable (Guisos)?", value=False)
    is_configurable_salsa_chk = ft.Checkbox(label="¿Platillo Configurable (Salsas)?", value=False)

    search_field = ft.TextField(
        hint_text="Buscar platillo...",
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: cargar_menu_admin(e.control.value),
        border_radius=20, height=40,
        text_size=14, content_padding=10, filled=True,
    )

    imagen_path = ft.Text(visible=False)
    imagen_preview = ft.Image(src="", width=100, height=100, fit="cover", visible=False)
    upload_status = ft.Text()

    # =====================================================
    #   MANEJADOR MEJORADO PARA GUARDADO DE IMÁGENES
    # =====================================================
    def on_file_picked(files):
        """Procesa los archivos seleccionados."""
        if files:
            archivo = files[0]
            upload_status.value = "Procesando imagen..."
            page.update()

            try:
                assets_dir = os.path.abspath(os.path.join(os.getcwd(), "app/src/assets"))
                if not os.path.exists(assets_dir):
                    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
                
                os.makedirs(assets_dir, exist_ok=True)

                ext = os.path.splitext(archivo.name)[1]
                nuevo_nombre = f"{uuid.uuid4()}{ext}"
                destino = os.path.join(assets_dir, nuevo_nombre)

                if hasattr(archivo, "path") and archivo.path:
                    try:
                        shutil.copy(archivo.path, destino)
                        finalizar_guardado(nuevo_nombre)
                        return
                    except Exception:
                        pass

                upload_url = page.get_upload_url(archivo.name, 600)
                file_picker.upload([ft.FilePickerUploadFile(archivo.name, upload_url=upload_url)])
                upload_status.value = "Subiendo imagen (método web)..."
                page.update()

            except Exception as ex:
                upload_status.value = f"Error general: {ex}"
                page.update()
        else:
            upload_status.value = "Selección cancelada."
            page.update()

    def finalizar_guardado(nombre_archivo):
        """Actualiza la UI una vez que la imagen está en assets."""
        imagen_path.value = nombre_archivo
        import time
        imagen_preview.src = f"src/assets/{nombre_archivo}?{time.time()}"
        imagen_preview.visible = True
        upload_status.value = "Imagen guardada correctamente ✔"
        page.update()

    def show_snackbar(text):
        b = ft.SnackBar(ft.Text(text))
        page.overlay.append(b)
        b.open = True
        page.update()

    # ===========================
    # MOSTRAR LISTA DEL MENÚ
    # ===========================
    def cargar_menu_admin(search_term=None):
        lista.controls.clear()
        platillos = obtener_menu(solo_activos=False, search_term=search_term)

        if not platillos:
            lista.controls.append(ft.Text("No hay platillos que coincidan 🍽️"))
        else:
            for pid, nombre, desc, precio, imagen, activo, descuento, is_conf, is_conf_salsa, piezas in platillos:
                def toggle_vis(e, id=pid):
                    actualizar_visibilidad_platillo(id, e.control.value)

                precio_texto = f"${precio:.2f}"
                if descuento > 0:
                    precio_final = precio * (1 - descuento / 100)
                    precio_texto = f"${precio:.2f} -> ${precio_final:.2f} (-{descuento}%)"
                
                conf_labels = []
                if is_conf: conf_labels.append("Guisos")
                if is_conf_salsa: conf_labels.append("Salsas")
                conf_text = f" ({', '.join(conf_labels)})" if conf_labels else ""
                
                piezas_text = f" | {piezas} pz/orden" if piezas > 1 else ""

                lista.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Image(
                                        src=f"/{imagen}" if imagen else "",
                                        width=50, height=50,
                                        fit="cover"
                                    ) if imagen else ft.Container(width=50, height=50),
                                    ft.Column([
                                        ft.Text(f"{nombre}{conf_text}", size=18, weight="bold"),
                                        ft.Text(f"{precio_texto}{piezas_text}"),
                                    ]),
                                ]),
                                ft.Text(desc or "Sin descripción"),
                                ft.DataTable(
                                    columns=[ft.DataColumn(ft.Text("")), ft.DataColumn(ft.Text("")), ft.DataColumn(ft.Text(""))],
                                    rows=[
                                        ft.DataRow(cells=[
                                            ft.DataCell(ft.IconButton(
                                                icon=ft.Icons.EDIT,
                                                on_click=lambda e, id=pid, n=nombre, d=desc, p=precio, img=imagen, desc_val=descuento, ic=is_conf, ics=is_conf_salsa, pz=piezas:
                                                    preparar_edicion(id, n, d, p, img, desc_val, ic, ics, pz)
                                            )),
                                            ft.DataCell(ft.IconButton(
                                                icon=ft.Icons.DELETE,
                                                icon_color=ft.Colors.RED,
                                                on_click=lambda e, id=pid: confirmar_eliminacion(id)
                                            )),
                                            ft.DataCell(ft.Switch(
                                                value=bool(activo),
                                                on_change=toggle_vis,
                                                active_color=ft.Colors.GREEN_700,
                                            )),
                                        ])
                                    ]
                                )
                            ])
                        )
                    )
                )
        page.update()

    editing_id = None

    def limpiar():
        nonlocal editing_id
        editing_id = None
        nombre_field.value = ""
        descripcion_field.value = ""
        precio_field.value = ""
        descuento_field.value = "0"
        piezas_field.value = "1"
        is_configurable_chk.value = False
        is_configurable_salsa_chk.value = False
        imagen_path.value = ""
        imagen_preview.visible = False
        upload_status.value = ""
        btn_guardar.text = "Guardar nuevo platillo"
        page.update()

    def preparar_edicion(pid, nombre, desc, precio, imagen, descuento, is_conf, is_conf_salsa, piezas):
        nonlocal editing_id
        editing_id = pid
        nombre_field.value = nombre
        descripcion_field.value = desc
        precio_field.value = str(precio)
        descuento_field.value = str(descuento)
        piezas_field.value = str(piezas)
        is_configurable_chk.value = bool(is_conf)
        is_configurable_salsa_chk.value = bool(is_conf_salsa)
        imagen_path.value = imagen or ""
        if imagen:
            imagen_preview.src = f"/{imagen}"
            imagen_preview.visible = True
        else:
            imagen_preview.visible = False
        btn_guardar.text = "Actualizar platillo"
        page.update()

    def guardar_o_actualizar(e):
        nonlocal editing_id
        n, d, precio_str, descuento_str, piezas_str = nombre_field.value.strip(), descripcion_field.value.strip(), precio_field.value.strip(), descuento_field.value.strip(), piezas_field.value.strip()
        img = imagen_path.value
        is_conf = 1 if is_configurable_chk.value else 0
        is_conf_salsa = 1 if is_configurable_salsa_chk.value else 0

        if not n or not precio_str:
            show_snackbar("Nombre y precio son obligatorios")
            return
        try:
            precio, descuento = float(precio_str), float(descuento_str) if descuento_str else 0
            piezas = int(piezas_str) if piezas_str else 1
            if piezas < 1: piezas = 1
        except:
            show_snackbar("Valores numéricos inválidos")
            return
        if editing_id:
            actualizar_platillo(editing_id, n, d, precio, img, descuento, is_conf, is_conf_salsa, piezas)
            show_snackbar("Platillo actualizado ✔")
        else:
            agregar_platillo(n, d, precio, img, descuento, is_conf, is_conf_salsa, piezas)
            show_snackbar("Platillo agregado ✔")
        limpiar()
        cargar_menu_admin()

    def confirmar_eliminacion(pid):
        def _ok(e):
            eliminar_platillo(pid)
            dlg.open = False
            cargar_menu_admin()
            show_snackbar("Platillo eliminado 🗑️")
            page.update()
        dlg = ft.AlertDialog(
            title=ft.Text("Eliminar"),
            content=ft.Text("¿Seguro que deseas eliminar este platillo?"),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg, "open", False) or page.update()), ft.TextButton("Eliminar", on_click=_ok)]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def confirmar_ocultar_todos(e):
        def _ok_ocultar(e):
            ocultar_todos_los_platillos()
            dlg_hide.open = False
            cargar_menu_admin()
            show_snackbar("Todos los platillos han sido ocultados.")
            page.update()
        dlg_hide = ft.AlertDialog(
            title=ft.Text("Ocultar Todos"),
            content=ft.Text("¿Seguro que deseas ocultar TODOS los platillos del menú público?"),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg_hide, "open", False) or page.update()), ft.TextButton("Ocultar Todos", on_click=_ok_ocultar, style=ft.ButtonStyle(color=ft.Colors.RED))]
        )
        page.overlay.append(dlg_hide)
        dlg_hide.open = True
        page.update()

    def confirmar_mostrar_todos(e):
        def _ok_mostrar(e):
            mostrar_todos_los_platillos()
            dlg_show.open = False
            cargar_menu_admin()
            show_snackbar("Todos los platillos ahora están visibles.")
            page.update()
        dlg_show = ft.AlertDialog(
            title=ft.Text("Mostrar Todos"),
            content=ft.Text("¿Deseas hacer visibles TODOS los platillos en el menú público?"),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(dlg_show, "open", False) or page.update()), ft.TextButton("Mostrar Todos", on_click=_ok_mostrar, style=ft.ButtonStyle(color=ft.Colors.GREEN))]
        )
        page.overlay.append(dlg_show)
        dlg_show.open = True
        page.update()

    btn_guardar = ft.Button(content=ft.Text("Guardar nuevo platillo"), on_click=guardar_o_actualizar)
    btn_ocultar_todos = ft.FilledButton(
        content=ft.Text("Ocultar Todos"), 
        icon=ft.Icons.VISIBILITY_OFF, 
        style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE), 
        on_click=confirmar_ocultar_todos
    )
    btn_mostrar_todos = ft.FilledButton(
        content=ft.Text("Mostrar Todos"), 
        icon=ft.Icons.VISIBILITY, 
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE), 
        on_click=confirmar_mostrar_todos
    )

    cargar_menu_admin()

    async def pick_image_file(e):
        files = await file_picker.pick_files(allow_multiple=False)
        on_file_picked(files)

    content_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Gestión del menú", size=20, weight="bold"),
                nombre_field, descripcion_field, precio_field, descuento_field, piezas_field,
                ft.Text("Opciones de configuración:", size=14, weight="bold"),
                ft.Column([is_configurable_chk, is_configurable_salsa_chk], spacing=0), 
                ft.Row([
                    ft.Button(content=ft.Text("Imagen"), icon=ft.Icons.UPLOAD_FILE, on_click=pick_image_file, expand=True),
                    imagen_preview
                ], scroll="auto"),
                upload_status,
                            ft.Row([
                                ft.FilledButton(
                                    content=ft.Text("Guardar"), 
                                    on_click=guardar_o_actualizar, 
                                    expand=True,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.BROWN_700, color=ft.Colors.WHITE)
                                ), 
                                ft.FilledButton(
                                    content=ft.Text("Cancelar"), 
                                    on_click=lambda e: limpiar(), 
                                    expand=True,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                                )
                            ], scroll="auto"),                ft.Divider(),
                ft.Text("Platillos registrados:", size=18, weight="bold"),
                search_field,
                ft.Row([btn_mostrar_todos, btn_ocultar_todos], alignment=ft.MainAxisAlignment.END, scroll="auto"),
                lista # La lista ya es un Column con expand=True
            ],
            spacing=15,
        ),
        padding=20,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=15,
    )

    return ft.Column([content_container], expand=True, scroll="auto")
