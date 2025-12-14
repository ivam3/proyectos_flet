import flet as ft
import os
import uuid
import httpx
from database import (
    obtener_menu,
    agregar_platillo,
    actualizar_platillo,
    eliminar_platillo,
    actualizar_visibilidad_platillo,
)

def menu_admin_view(page: ft.Page):

    lista = ft.Column(scroll="auto")

    nombre_field = ft.TextField(label="Nombre del platillo")
    descripcion_field = ft.TextField(label="Descripción", multiline=True)
    precio_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER)

    imagen_path = ft.Text(visible=False)
    imagen_preview = ft.Image(src="", width=100, height=100, fit="cover", visible=False)
    upload_status = ft.Text()

    # =====================================================
    #   MANEJADOR ÚNICO PARA SELECCIÓN Y SUBIDA DE ARCHIVOS
    # =====================================================
    def on_upload(e: ft.FilePickerUploadEvent):
        if e.files: # El evento indica que se seleccionaron archivos
            if not e.files:
                return
            archivo = e.files[0]
            try:
                # Obtenemos URL temporal para subir archivo al buffer de Flet Web
                upload_url = page.get_upload_url(archivo.name, 600)
                file_picker.upload([ft.FilePickerUploadFile(archivo.name, upload_url=upload_url)])
                upload_status.value = "Subiendo imagen..."
            except Exception as ex:
                upload_status.value = f"Error al pedir URL de subida: {ex}"
        elif e.error: # Hubo un error durante la subida (o selección)
            upload_status.value = f"Error: {e.error}"
        elif e.progress == 1.0: # Archivo completamente subido
            try:
                # Pedimos URL para descargar
                temp_url = page.get_upload_url(e.file_name)
                response = httpx.get(temp_url)
                response.raise_for_status()

                # Guardamos el archivo en /src/assets/
                assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
                os.makedirs(assets_dir, exist_ok=True)
                ext = os.path.splitext(e.file_name)[1]
                nuevo_nombre = f"{uuid.uuid4()}{ext}"
                destino = os.path.join(assets_dir, nuevo_nombre)
                with open(destino, "wb") as f:
                    f.write(response.content)

                imagen_path.value = nuevo_nombre
                imagen_preview.src = f"src/assets/{nuevo_nombre}"
                imagen_preview.visible = True
                upload_status.value = "Imagen cargada ✔"
            except Exception as ex:
                upload_status.value = f"Error al guardar archivo: {ex}"
        
        page.update()

    file_picker = ft.FilePicker(on_upload=on_upload)

    editing_id = None

    def show_snackbar(text):
        b = ft.SnackBar(ft.Text(text))
        page.overlay.append(b)
        b.open = True
        page.update()

    # ===========================
    # MOSTRAR LISTA DEL MENÚ
    # ===========================
    def cargar_menu_admin():
        lista.controls.clear()

        platillos = obtener_menu(solo_activos=False)

        if not platillos:
            lista.controls.append(ft.Text("No hay platillos registrados 🍽️"))
        else:
            for pid, nombre, desc, precio, imagen, activo in platillos:

                def toggle_vis(e, id=pid, status=activo):
                    actualizar_visibilidad_platillo(id, not status)
                    cargar_menu_admin()

                lista.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Image(
                                        src=f"src/assets/{imagen}" if imagen else "",
                                        width=50, height=50,
                                        fit="cover"
                                    ) if imagen else ft.Container(width=50, height=50),

                                    ft.Column([
                                        ft.Text(nombre, size=18, weight="bold"),
                                        ft.Text(f"${precio:.2f}"),
                                    ]),
                                ]),
                                ft.Text(desc or "Sin descripción"),

                                ft.DataTable(
                                    columns=[
                                        ft.DataColumn(ft.Text("")), # Placeholder for Edit button
                                        ft.DataColumn(ft.Text("")), # Placeholder for Delete button
                                        ft.DataColumn(ft.Text("")), # Placeholder for Switch
                                    ],
                                    rows=[
                                        ft.DataRow(
                                            cells=[
                                                ft.DataCell(ft.IconButton(
                                                    icon=ft.Icons.EDIT,
                                                    tooltip="Editar",
                                                    on_click=lambda e, id=pid, n=nombre, d=desc,
                                                                    p=precio, img=imagen:
                                                        preparar_edicion(id, n, d, p, img)
                                                )),
                                                ft.DataCell(ft.IconButton(
                                                    icon=ft.Icons.DELETE,
                                                    tooltip="Eliminar",
                                                    icon_color=ft.Colors.RED,
                                                    on_click=lambda e, id=pid:
                                                        confirmar_eliminacion(id)
                                                )),
                                                ft.DataCell(ft.Switch(
                                                    value=activo,
                                                    on_change=toggle_vis,
                                                    width=50,  # Example width
                                                    height=25, # Example height
                                                    active_color=ft.Colors.GREEN_700,
                                                    inactive_thumb_color=ft.Colors.GREY_500,
                                                    inactive_track_color=ft.Colors.BLUE_GREY_100,
                                                )),
                                            ]
                                        )
                                    ]
                                )
                            ])
                        )
                    )
                )

        page.update()

    # ===========================
    # GUARDAR O ACTUALIZAR
    # ===========================
    def guardar_o_actualizar(e):
        nonlocal editing_id

        n = nombre_field.value.strip()
        d = descripcion_field.value.strip()
        precio_str = precio_field.value.strip()
        img = imagen_path.value

        if not n or not precio_str:
            show_snackbar("Nombre y precio son obligatorios")
            return

        try:
            precio = float(precio_str)
        except:
            show_snackbar("Precio inválido")
            return

        if editing_id:
            actualizar_platillo(editing_id, n, d, precio, img)
            show_snackbar("Platillo actualizado ✔")
        else:
            agregar_platillo(n, d, precio, img)
            show_snackbar("Platillo agregado ✔")

        limpiar()
        cargar_menu_admin()

    # ===========================
    # EDITAR
    # ===========================
    def preparar_edicion(pid, nombre, desc, precio, imagen):
        nonlocal editing_id
        editing_id = pid

        nombre_field.value = nombre
        descripcion_field.value = desc
        precio_field.value = str(precio)
        imagen_path.value = imagen or ""

        if imagen:
            imagen_preview.src = f"src/assets/{imagen}"
            imagen_preview.visible = True
        else:
            imagen_preview.visible = False

        btn_guardar.text = "Actualizar platillo"
        page.update()

    # ===========================
    # ELIMINAR
    # ===========================
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
            actions=[
                ft.TextButton("Cancelar",
                              on_click=lambda e: setattr(dlg, "open", False)),
                ft.TextButton("Eliminar", on_click=_ok)
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ===========================
    # LIMPIAR FORMULARIO
    # ===========================
    def limpiar():
        nonlocal editing_id
        editing_id = None

        nombre_field.value = ""
        descripcion_field.value = ""
        precio_field.value = ""
        imagen_path.value = ""
        imagen_preview.visible = False
        upload_status.value = ""
        btn_guardar.text = "Guardar nuevo platillo"

        page.update()

    btn_guardar = ft.Button(
        content=ft.Text("Guardar nuevo platillo"),
        on_click=guardar_o_actualizar
    )

    cargar_menu_admin()

    async def pick_image_file(e):
        await file_picker.pick_files(on_result=on_file_picked, allow_multiple=False)

    return ft.Column(
        expand=True,
        scroll="auto",
        controls=[
            ft.Text("Gestión del menú", size=20, weight="bold"),
            nombre_field,
            descripcion_field,
            precio_field,

            ft.Row([
                ft.Button(
                    content=ft.Text("Seleccionar imagen"),
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=pick_image_file,
                ),
                imagen_preview
            ]),

            upload_status,

            ft.Row([
                btn_guardar,
                ft.Button(content=ft.Text("Cancelar"), on_click=lambda e: limpiar())
            ]),

            ft.Divider(),
            ft.Text("Platillos registrados:", size=18, weight="bold"),
            lista
        ]
    )
