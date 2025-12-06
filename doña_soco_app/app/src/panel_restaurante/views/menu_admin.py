import flet as ft
import os
import uuid
import shutil
from database import (
    obtener_menu,
    agregar_platillo,
    actualizar_platillo,
    eliminar_platillo,
    actualizar_visibilidad_platillo,
)


def menu_admin_view(page: ft.Page):
    """Panel para gestionar el menú del restaurante."""

    lista = ft.Column()
    nombre_field = ft.TextField(label="Nombre del platillo")
    descripcion_field = ft.TextField(label="Descripción", multiline=True)
    precio_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER)

    # Campos de imagen
    imagen_path = ft.Text(visible=False)
    imagen_preview = ft.Image(width=100, height=100, fit=ft.ImageFit.COVER, visible=False)
    upload_status = ft.Text()

    # -------------------------------------------------------------------------
    #  MANEJO DE ARCHIVO → COMPATIBLE CON ANDROID, WINDOWS, LINUX, iOS, WEB
    # -------------------------------------------------------------------------
    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        archivo = e.files[0]

        try:
            # Leer contenido binario del archivo (Android friendly)
            contenido = archivo.file.read()
            if not contenido:
                upload_status.value = "Error: no se pudo leer el contenido del archivo."
                page.update()
                return

            # Carpeta assets absoluta
            assets_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../assets")
            )
            os.makedirs(assets_dir, exist_ok=True)

            # Generar nombre único
            _, ext = os.path.splitext(archivo.name)
            nuevo_nombre = f"{uuid.uuid4()}{ext}"
            destino = os.path.join(assets_dir, nuevo_nombre)

            # Guardar la imagen
            with open(destino, "wb") as f:
                f.write(contenido)

            # Actualizar UI
            imagen_path.value = nuevo_nombre
            imagen_preview.src = f"/assets/{nuevo_nombre}"
            imagen_preview.visible = True
            upload_status.value = "Imagen guardada correctamente."

            page.update()

        except Exception as ex:
            upload_status.value = f"Error al guardar archivo: {ex}"
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # Estado de edición
    editing_id = None

    # Snackbar
    def show_snackbar(text):
        snack = ft.SnackBar(ft.Text(text))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # -------------------------------------------------------------------------
    #  LISTAR PLATILLOS
    # -------------------------------------------------------------------------
    def cargar_menu_admin():
        lista.controls.clear()
        platillos = obtener_menu(solo_activos=False)

        if not platillos:
            lista.controls.append(ft.Text("No hay platillos registrados 🍽️"))
        else:
            for p in platillos:
                pid, nombre, desc, precio, imagen, is_active = p

                def _toggle_vis(e, id=pid, status=is_active):
                    actualizar_visibilidad_platillo(id, not status)
                    cargar_menu_admin()
                    show_snackbar(f"Cambiado: {nombre}")

                lista.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column([
                                ft.Row([
                                    ft.Image(
                                        src=f"/assets/{imagen}",
                                        width=50,
                                        height=50,
                                        fit=ft.ImageFit.COVER,
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
                                            preparar_edicion(id, n, d, p, img),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar",
                                        icon_color=ft.Colors.RED_400,
                                        on_click=lambda e, id=pid: confirmar_eliminacion(id),
                                    ),
                                    ft.Switch(
                                        label="Visible" if is_active else "Oculto",
                                        value=is_active,
                                        on_change=_toggle_vis,
                                    ),
                                ], spacing=10),
                            ]),
                        ),
                    )
                )
        page.update()

    # -------------------------------------------------------------------------
    #  GUARDAR / ACTUALIZAR PLATILLO
    # -------------------------------------------------------------------------
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
        except:
            show_snackbar("El precio debe ser numérico ❗")
            return

        if editing_id:
            actualizar_platillo(editing_id, nombre, descripcion, precio, imagen)
            show_snackbar("Platillo actualizado ✅")
        else:
            agregar_platillo(nombre, descripcion, precio, imagen)
            show_snackbar("Platillo guardado exitosamente ✅")

        limpiar()
        cargar_menu_admin()

    # -------------------------------------------------------------------------
    #  EDITAR
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    #  ELIMINAR
    # -------------------------------------------------------------------------
    def confirmar_eliminacion(pid):
        def _del(e):
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
                ft.TextButton("Eliminar", on_click=_del),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # -------------------------------------------------------------------------
    #  LIMPIAR CAMPOS
    # -------------------------------------------------------------------------
    def limpiar():
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

    # Carga inicial
    cargar_menu_admin()

    return ft.Column(
        expand=True,
        scroll='auto',
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
                        allow_multiple=False
                    ),
                ),
                imagen_preview,
            ]),

            upload_status,

            ft.Row([
                btn_guardar,
                ft.ElevatedButton("Cancelar edición", on_click=lambda e: limpiar()),
            ]),

            ft.Divider(height=20),
            ft.Text("Lista de platillos", size=20, weight="bold"),

            lista,
        ],
    )
