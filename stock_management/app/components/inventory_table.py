import flet as ft
from components.photo_viewer import photo_viewer
from components.sale_dialog import sale_dialog

def inventory_table(page: ft.Page, products, refresh_callback):

    if not products:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=50, color=ft.Colors.GREY_400),
                    ft.Text("El inventario está vacío", size=18, color=ft.Colors.GREY_600, weight="bold"),
                    ft.Text("Agregue un producto arriba para comenzar", size=14, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=50,
            width=float("inf"),
        )

    api = page.session.api

    async def on_file_result(file, product_id):
        if not file: return
        if hasattr(file, "bytes") and file.bytes: content = file.bytes
        else:
            with open(file.path, "rb") as f: content = f.read()
        
        if api.upload_photo(product_id, file.name, content):
            show_toast("Éxito", "Foto subida correctamente", ft.Colors.GREEN)
            refresh_callback()
        else:
            show_toast("Error", "No se pudo subir la foto", ft.Colors.RED)

    def confirm_delete(product_id, model_name):
        def do_delete(e):
            if api.delete_product(product_id):
                show_toast("Eliminado", f"Producto {model_name} eliminado", ft.Colors.ORANGE_700)
                dlg.open = False
                refresh_callback()
            else:
                show_toast("Error", "No se pudo eliminar", ft.Colors.RED)
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Estás seguro de eliminar '{model_name}'? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or page.update()),
                ft.Button("Eliminar", on_click=do_delete, bgcolor=ft.Colors.RED, color="white"),
            ],        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def start_edit(product):
        page.session.edit_request = product
        if hasattr(page.session, "switch_tab"):
            page.session.switch_tab(1) # Ir a Registro

    def start_upload(product_id):
        page.session.file_picker_ctx = {"callback": lambda f: on_file_result(f, product_id)}
        page.session.file_picker.pick_files(file_type=ft.FilePickerFileType.IMAGE)

    def show_toast(title, message, color):
        page.snack_bar = ft.SnackBar(ft.Text(f"{title}: {message}"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    rows = []
    for p in products:
        # 1. Construir el Mapa de Variantes (Color -> Talla -> Info)
        variant_map = {}
        for s in p.get('sizes', []):
            color = str(s.get('color', 'N/A')).strip()
            size = str(s.get('size', '')).strip()
            if color not in variant_map:
                variant_map[color] = {}
            variant_map[color][size] = {
                "stock": s.get('stock', 0),
                "id": s.get('id')
            }

        available_colors = sorted(list(variant_map.keys()))
        
        # 2. Definir Controles de la Fila
        stock_text = ft.Text("0", weight="bold", size=14)
        
        # Dropdown de Tallas (se poblará según el color seleccionado)
        size_dd = ft.Dropdown(
            width=100, height=40, text_size=12, content_padding=5,
        )

        def update_stock(e=None, v_map=variant_map, s_txt=stock_text, c_dd=None, s_dd=None):
            color = c_dd.value if c_dd else "N/A"
            size = s_dd.value if s_dd else ""
            
            data = v_map.get(color, {}).get(size, {"stock": 0})
            s_txt.value = str(data["stock"])
            s_txt.color = ft.Colors.ORANGE_700 if data["stock"] > 0 else ft.Colors.RED_400
            try:
                s_txt.update()
            except: pass

        def update_sizes(e=None, v_map=variant_map, s_dd=size_dd, c_dd=None):
            selected_color = c_dd.value if c_dd else "N/A"
            # Obtenemos tallas para ese color y las ordenamos
            sizes = sorted(list(v_map.get(selected_color, {}).keys()))
            
            # Actualizar opciones del dropdown de tallas
            s_dd.options = [ft.dropdown.Option(s) for s in sizes]
            s_dd.value = sizes[0] if sizes else None
            
            # Una vez actualizadas las tallas, actualizamos el stock mostrado
            update_stock(v_map=v_map, c_dd=c_dd, s_dd=s_dd)
            try:
                s_dd.update()
            except: pass

        # Dropdown de Colores
        color_dd = ft.Dropdown(
            options=[ft.dropdown.Option(c) for c in available_colors],
            value=available_colors[0] if available_colors else "N/A",
            width=120, height=40, text_size=12, content_padding=5,
        )
        
        # Vincular Eventos con lambdas para pasar referencias correctas de esta fila
        color_dd.on_change = lambda e, vm=variant_map, sd=size_dd, cd=color_dd: update_sizes(e, vm, sd, cd)
        size_dd.on_change = lambda e, vm=variant_map, cd=color_dd, sd=size_dd: update_stock(e, vm, stock_text, cd, sd)

        # 3. Inicialización Manual de los valores antes de añadir a la tabla
        # Esto asegura que aparezcan con datos desde el primer render
        if available_colors:
            first_color = available_colors[0]
            first_color_sizes = sorted(list(variant_map.get(first_color, {}).keys()))
            size_dd.options = [ft.dropdown.Option(s) for s in first_color_sizes]
            if first_color_sizes:
                size_dd.value = first_color_sizes[0]
                first_stock = variant_map[first_color][size_dd.value]["stock"]
                stock_text.value = str(first_stock)
                stock_text.color = ft.Colors.ORANGE_700 if first_stock > 0 else ft.Colors.RED_400

        num_photos = len(p.get('photos', []))

        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(p['model_name'], weight="bold")),
                    ft.DataCell(ft.Text(p['sku'] or "N/A")),
                    ft.DataCell(ft.Text(f"${p['price']:.2f}", color=ft.Colors.GREEN_800, weight="bold")),
                    ft.DataCell(color_dd),
                    ft.DataCell(size_dd),
                    ft.DataCell(stock_text),
                    ft.DataCell(
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    tooltip="Editar Info",
                                    icon_color=ft.Colors.BLUE_700,
                                    on_click=lambda _, prod=p: start_edit(prod)
                                ),
                                ft.Stack([
                                    ft.IconButton(
                                        icon=ft.Icons.IMAGE_OUTLINED,
                                        icon_color=ft.Colors.BLACK,
                                        tooltip="Ver Fotos",
                                        on_click=lambda _, prod=p: photo_viewer(page, prod, refresh_callback)
                                    ),
                                    ft.Container(
                                        content=ft.Text(str(num_photos), size=9, color="white", weight="bold"),
                                        bgcolor=ft.Colors.ORANGE_700, padding=2, border_radius=10,
                                        right=0, top=0, visible=num_photos > 0
                                    )
                                ]),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_A_PHOTO_OUTLINED,
                                    icon_color=ft.Colors.BLUE_GREY_700,
                                    tooltip="Subir Foto",
                                    on_click=lambda _, pid=p['id']: start_upload(pid)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SHOPPING_BAG_OUTLINED,
                                    tooltip="Vender / Apartar",
                                    icon_color=ft.Colors.GREEN_700,
                                    on_click=lambda _, prod=p: sale_dialog(page, prod, refresh_callback)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    on_click=lambda e, pid=p['id'], name=p['model_name']: confirm_delete(pid, name)
                                ),
                            ],
                            spacing=0
                        )
                    ),
                ]
            )
        )

    return ft.Row(
        [
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Modelo")),
                    ft.DataColumn(ft.Text("SKU")),
                    ft.DataColumn(ft.Text("Precio")),
                    ft.DataColumn(ft.Text("Color")),
                    ft.DataColumn(ft.Text("Talla")),
                    ft.DataColumn(ft.Text("Stock")),
                    ft.DataColumn(ft.Text("Acciones")),
                ],
                rows=rows,
                heading_row_color=ft.Colors.GREY_100,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                vertical_lines=ft.BorderSide(1, ft.Colors.GREY_300),
            )
        ],
        scroll=ft.ScrollMode.ALWAYS
    )
