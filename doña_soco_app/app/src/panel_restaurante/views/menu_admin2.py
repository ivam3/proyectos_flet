import flet as ft
import os
import uuid
import httpx
import shutil # Se requiere para carga de archivos en version Termux
from database import (
    obtener_menu,
    agregar_platillo,
    actualizar_platillo,
    eliminar_platillo,
    actualizar_visibilidad_platillo
)

def menu_admin_view(page: ft.Page):
    """Panel para gestionar el menú del restaurante."""
    lista = ft.Column(scroll="auto", expand=True)
    nombre_field = ft.TextField(label="Nombre del platillo")
    descripcion_field = ft.TextField(label="Descripción", multiline=True)
    precio_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER)

    # --- Lógica de carga de imagen ---
    imagen_path = ft.Text(visible=False)  # Guarda el archivo final
    imagen_preview = ft.Image(width=100, height=100, fit=ft.ImageFit.COVER, visible=False)
    upload_status = ft.Text()

    # --- Lógica de carga de imagen (versión Termux compatible) ---
    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        archivo = e.files[0]  # solo uno

        origen = archivo.path  # <- ruta real en Android / Termux
        if not origen:
            upload_status.value = "Error: no se pudo obtener la ruta del archivo."
            page.update()
            return

        try:
            # Carpeta destino: src/assets
            assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
            os.makedirs(assets_dir, exist_ok=True)

            # Crear nombre único
            ext = os.path.splitext(origen)[1]
            nuevo_nombre = f"{uuid.uuid4()}{ext}"
            destino = os.path.join(assets_dir, nuevo_nombre)

            # Copiar archivo
            shutil.copy(origen, destino)

            # Actualizar UI
            imagen_path.value = nuevo_nombre
            imagen_preview.src = f"/assets/{nuevo_nombre}"
            imagen_preview.visible = True
            upload_status.value = "Imagen guardada correctamente."

            page.update()

        except Exception as ex:
            upload_status.value = f"Error al copiar archivo: {ex}"
            page.update()


    # FilePicker sin uploads
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
#############################################
#  CARGA DE IMAGEN (versión Flet estándar)  #
#############################################
    # def on_file_picked(e: ft.FilePickerResultEvent):
    #     if e.files:
    #         upload_list = []
    #         for f in e.files:
    #             upload_list.append(
    #                 ft.FilePickerUploadFile(
    #                     f.name,
    #                     upload_url=page.get_upload_url(f.name, 600),
    #                 )
    #             )
    #         file_picker.upload(upload_list)
    #         upload_status.value = "Subiendo imagen..."
    #         page.update()
    #
    # def on_upload(e: ft.FilePickerUploadEvent):
    #     if e.error:
    #         upload_status.value = f"Error al subir: {e.error}"
    #     elif e.progress == 1.0:
    #         temp_url = page.get_upload_url(e.file_name)
    #
    #         try:
    #             # Descargar archivo temporal de Flet
    #             response = httpx.get(temp_url)
    #             response.raise_for_status()
    #
    #             # Guardarlo en /assets/
    #             assets_dir = os.path.abspath(
    #                 os.path.join(os.path.dirname(__file__), "../../assets")
    #             )
    #             os.makedirs(assets_dir, exist_ok=True)
    #
    #             unique_filename = f"{uuid.uuid4()}{os.path.splitext(e.file_name)[1]}"
    #             destination_path = os.path.join(assets_dir, unique_filename)
    #
    #             with open(destination_path, "wb") as f:
    #                 f.write(response.content)
    #
    #             # Actualizar UI
    #             imagen_path.value = unique_filename
    #             imagen_preview.src = f"/assets/{unique_filename}"
    #             imagen_preview.visible = True
    #             upload_status.value = "Imagen cargada correctamente."
    #
    #         except Exception as ex:
    #             upload_status.value = f"Error al procesar: {ex}"
    #
    #     page.update()
    #
    # file_picker = ft.FilePicker(on_result=on_file_picked, on_upload=on_upload)
    # page.overlay.append(file_picker)
    # ---------------------------------

    editing_id = None

    def show_snackbar(text):
        snack_bar = ft.SnackBar(ft.Text(text))
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()

    def cargar_menu_admin():
        lista.controls.clear()
        platillos = obtener_menu(solo_activos=False)

        if not platillos:
            lista.controls.append(ft.Text("No hay platillos registrados 🍽️"))
        else:
            for p in platillos:
                pid, nombre, desc, precio, imagen, is_active = p

                # Cambio de visibilidad
                def _toggle_visibility(e, id=pid, current_status=is_active):
                    actualizar_visibilidad_platillo(id, not current_status)
                    cargar_menu_admin()
                    show_snackbar(f"Cambiado: {nombre}")

                lista.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Image(src=f"/assets/{imagen}",
                                             width=50, height=50,
                                             fit=ft.ImageFit.COVER
                                    ) if imagen else ft.Container(width=50, height=50),
                                    ft.Column([
                                        ft.Text(nombre, size=18, weight="bold"),
                                        ft.Text(f"${precio:.2f}", size=16),
                                    ]),
                                ], alignment=ft.MainAxisAlignment.START),
                                ft.Text(desc or "Sin descripción"),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Editar",
                                        on_click=lambda e, id=pid, n=nombre, d=desc, p=precio, img=imagen:
                                            preparar_edicion(id, n, d, p, img)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar",
                                        icon_color=ft.Colors.RED_400,
                                        on_click=lambda e, id=pid: confirmar_eliminacion(id)
                                    ),
                                    ft.Switch(
                                        label="Visible" if is_active else "Oculto",
                                        value=is_active,
                                        on_change=_toggle_visibility
                                    )
                                ], spacing=10)
                            ])
                        )
                    )
                )
        page.update()

    def guardar_o_actualizar(e):
        nonlocal editing_id
        nombre = nombre_field.value.strip()
        descripcion = descripcion_field.value.strip()
        precio_str = precio_field.value.strip()
        imagen = imagen_path.value

        if not nombre or not precio_str:
            show_snackbar("Nombre y precio son obligatorios ❗")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            show_snackbar("El precio debe ser numérico ❗")
            return

        if editing_id is not None:
            actualizar_platillo(editing_id, nombre, descripcion, precio, imagen)
            show_snackbar("Platillo actualizado ✅")
        else:
            agregar_platillo(nombre, descripcion, precio, imagen)
            show_snackbar("Platillo guardado exitosamente ✅")

        limpiar_campos_y_resetear_estado()
        cargar_menu_admin()

    def preparar_edicion(pid, nombre, desc, precio, imagen):
        nonlocal editing_id
        editing_id = pid

        nombre_field.value = nombre
        descripcion_field.value = desc
        precio_field.value = str(precio)
        imagen_path.value = imagen or ""

        if imagen:
            imagen_preview.src = f"/assets/{imagen}"
            imagen_preview.visible = True
        else:
            imagen_preview.visible = False

        btn_guardar.text = "Actualizar platillo"
        page.update()

    def confirmar_eliminacion(pid):
        def _eliminar_confirmado(e):
            eliminar_platillo(pid)
            dialog.open = False
            cargar_menu_admin()
            show_snackbar("Platillo eliminado 🗑️")
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text("¿Estás seguro?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.TextButton("Eliminar", on_click=_eliminar_confirmado),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def limpiar_campos_y_resetear_estado():
        nonlocal editing_id
        editing_id = None
        nombre_field.value = ""
        descripcion_field.value = ""
        precio_field.value = ""
        imagen_path.value = ""
        imagen_preview.src = None
        imagen_preview.visible = False
        upload_status.value = ""
        btn_guardar.text = "Guardar nuevo platillo"
        page.update()

    btn_guardar = ft.ElevatedButton("Guardar nuevo platillo", on_click=guardar_o_actualizar)

    cargar_menu_admin()

    return ft.Column(
        expand=True,
        controls=[
            ft.Text("Agregar o editar platillos", size=20, weight="bold"),
            nombre_field,
            descripcion_field,
            precio_field,
            ft.Row([
                ft.ElevatedButton(
                    "Seleccionar Imagen",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: file_picker.pick_files(
                        allow_multiple=False #,
                        # allowed_extensions=["png", "jpg", "jpeg"]
                    )
                ),
                imagen_preview,
            ]),
            upload_status,
            ft.Row([
                btn_guardar,
                ft.ElevatedButton("Cancelar edición", on_click=lambda e: limpiar_campos_y_resetear_estado())
            ]),
            ft.Divider(height=20),
            ft.Text("Lista de platillos", size=20, weight="bold"),
            lista,
        ]
    )
