import flet as ft

def product_form(page: ft.Page, on_success):
    
    api = page.session.api
    current_edit_id = None
    selected_photos = [] # Lista de {name, bytes}

    # ANCHO DE SEGURIDAD TOTAL PARA ANDROID (300px)
    FIELD_WIDTH = 300 
    
    field_style = {
        "width": FIELD_WIDTH,
        "border_radius": 8,
        "text_size": 14,
        "height": 55,
        "border_color": ft.Colors.BLUE_GREY_200
    }

    # Campos
    provider_input = ft.TextField(label="PROVEEDOR", **field_style)
    modelo_input = ft.TextField(label="MODELO", text_style=ft.TextStyle(weight="bold"), **field_style)
    sku_input = ft.TextField(label="SKU (Obligatorio)", **field_style)
    brand_input = ft.TextField(label="MARCA (Obligatorio)", **field_style)
    category_input = ft.TextField(label="CATEGORÍA", **field_style)
    
    gender_input = ft.Dropdown(
        label="GÉNERO",
        width=FIELD_WIDTH,
        border_radius=8,
        options=[
            ft.dropdown.Option("M", "Masculino"),
            ft.dropdown.Option("F", "Femenino"),
            ft.dropdown.Option("U", "Unisex"),
        ],
        value="U",
        text_size=14
    )
    
    tallas_input = ft.TextField(label="TALLAS (Obligatorio)", hint_text="Ej: 5 7 8", **field_style)
    color_input = ft.TextField(label="COLORES (Mapeo 1:1)", hint_text="Ej: Blanco Negro Rojo", **field_style)
    condition_input = ft.TextField(label="CONDICIÓN", hint_text="Nuevo, etc.", **field_style)
    
    costo_input = ft.TextField(label="COSTO ($ - Obligatorio)", keyboard_type=ft.KeyboardType.NUMBER, prefix=ft.Text("$ "), **field_style)
    tax_input = ft.TextField(label="TAX/ENVIO ($ - Obligatorio)", keyboard_type=ft.KeyboardType.NUMBER, value="0", prefix=ft.Text("$ "), **field_style)
    
    precio_input = ft.TextField(
        label="PRECIO VENTA FINAL ($ - Obligatorio)", 
        keyboard_type=ft.KeyboardType.NUMBER, 
        prefix=ft.Text("$ "),
        text_style=ft.TextStyle(weight="bold", color=ft.Colors.GREEN_700, size=16),
        **field_style
    )
    
    stocks_input = ft.TextField(label="CANTIDADES/STOCK (Obligatorio)", hint_text="Ej: 2 1 4", **field_style)

    title_text = ft.Text("DETALLES DEL PRODUCTO", weight="bold", size=18, color=ft.Colors.BLUE_GREY_900)
    photos_count_text = ft.Text("0 fotos seleccionadas", size=12, italic=True)

    def load_selected_photos(files):
        nonlocal selected_photos
        if not files: return
        
        # files puede ser una lista (multi) o un objeto único (depende del picker)
        file_list = files if isinstance(files, list) else [files]
        
        for f in file_list:
            try:
                if hasattr(f, "bytes") and f.bytes:
                    content = f.bytes
                else:
                    with open(f.path, "rb") as file_data:
                        content = file_data.read()
                selected_photos.append({"name": f.name, "bytes": content})
            except Exception as ex:
                print(f"Error cargando archivo {f.name}: {ex}")
        
        photos_count_text.value = f"{len(selected_photos)} fotos seleccionadas"
        photos_count_text.update()

    def pick_photos_click(_):
        page.session.file_picker_ctx = {
            "multi": True,
            "callback": load_selected_photos
        }
        page.session.file_picker.pick_files(
            allow_multiple=True, 
            file_type=ft.FilePickerFileType.IMAGE
        )

    photo_btn = ft.OutlinedButton(
        "SELECCIONAR FOTOS",
        icon=ft.Icons.IMAGE_SEARCH,
        on_click=pick_photos_click,
        width=FIELD_WIDTH
    )

    submit_btn = ft.Button(
        "GUARDAR INFORMACIÓN",
        icon=ft.Icons.SAVE,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLACK, 
            color=ft.Colors.WHITE,
            padding=20,
            shape=ft.RoundedRectangleBorder(radius=10)
        ),
        on_click=lambda e: on_submit(e),
        width=FIELD_WIDTH
    )
    
    cancel_btn = ft.TextButton(
        "CANCELAR EDICIÓN", 
        visible=False, 
        icon=ft.Icons.CANCEL,
        icon_color=ft.Colors.RED,
        on_click=lambda _: reset_form()
    )

    def show_alert(title, message, color=ft.Colors.BLACK):
        dlg = ft.AlertDialog(
            title=ft.Text(title, color=color, weight="bold"),
            content=ft.Text(message, color=ft.Colors.BLACK),
            actions=[
                ft.TextButton("Entendido", on_click=lambda e: [setattr(dlg, "open", False), page.update()])
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def reset_form():
        nonlocal current_edit_id, selected_photos
        current_edit_id = None
        selected_photos = []
        for field in [provider_input, modelo_input, sku_input, brand_input, category_input, 
                      tallas_input, color_input, condition_input, costo_input, tax_input, precio_input, stocks_input]:
            field.value = ""
        tax_input.value = "0"
        gender_input.value = "U"
        photos_count_text.value = "0 fotos seleccionadas"
        submit_btn.text = "GUARDAR INFORMACIÓN"
        cancel_btn.visible = False
        sku_input.disabled = False
        page.update()

    def on_submit(e):
        # 1. Validaciones
        missing = []
        if not sku_input.value: missing.append("SKU")
        if not tallas_input.value: missing.append("Talla")
        if not stocks_input.value: missing.append("Cantidad")
        if not costo_input.value: missing.append("Costo")
        if not precio_input.value: missing.append("Precio")

        if missing:
            show_alert("Campos Requeridos", f"Falta: {', '.join(missing)}", ft.Colors.RED)
            return

        # 2. Procesar Mapeo 1:1 (Talla, Stock, Color)
        raw_sizes = [s.strip() for s in tallas_input.value.split() if s.strip()]
        raw_stocks = [st.strip() for st in stocks_input.value.split() if st.strip()]
        raw_colors = [c.strip() for c in color_input.value.split() if c.strip()]
        
        initial_sizes = []
        try:
            for i, s in enumerate(raw_sizes):
                # Stock
                if len(raw_stocks) > i: stock_val = int(raw_stocks[i])
                elif len(raw_stocks) == 1: stock_val = int(raw_stocks[0])
                else: stock_val = 0
                
                # Color
                if len(raw_colors) > i: color_val = raw_colors[i]
                elif len(raw_colors) == 1: color_val = raw_colors[0]
                else: color_val = "N/A"

                initial_sizes.append({"size": s, "color": color_val, "stock": stock_val})
        except ValueError:
            show_alert("Error", "Cantidades deben ser números.", ft.Colors.RED)
            return

        # 3. Preparar datos
        product_data = {
            "model_name": modelo_input.value.upper() or "SIN NOMBRE",
            "provider": provider_input.value,
            "sku": sku_input.value,
            "brand": brand_input.value,
            "category": category_input.value,
            "gender": gender_input.value,
            "condition": condition_input.value,
            "cost": float(costo_input.value or 0),
            "tax": float(tax_input.value or 0),
            "price": float(precio_input.value or 0),
            "initial_sizes": initial_sizes
        }

        submit_btn.disabled = True
        submit_btn.text = "PROCESANDO..."
        page.update()

        if current_edit_id:
            res = api.update_product(current_edit_id, product_data)
        else:
            res = api.create_product(product_data)

        if res["success"]:
            # Subir fotos si es producto nuevo o edición
            new_pid = res["data"]["id"]
            for p_file in selected_photos:
                api.upload_photo(new_pid, p_file["name"], p_file["bytes"])
            
            show_alert("Éxito", "Producto guardado con éxito.", ft.Colors.GREEN)
            reset_form()
            on_success()
        else:
            show_alert("Error", res.get("error", "Fallo al guardar"), ft.Colors.RED)
        
        submit_btn.disabled = False
        submit_btn.text = "GUARDAR INFORMACIÓN"
        page.update()

    def load_product_for_edit(product):
        nonlocal current_edit_id
        current_edit_id = product['id']
        provider_input.value = product.get('provider', '')
        modelo_input.value = product['model_name']
        sku_input.value = product['sku']
        brand_input.value = product.get('brand', '')
        category_input.value = product.get('category', '')
        gender_input.value = product.get('gender', 'U')
        condition_input.value = product.get('condition', '')
        costo_input.value = str(product.get('cost', 0))
        tax_input.value = str(product.get('tax', 0))
        precio_input.value = str(product['price'])
        
        tallas_input.value = ""
        stocks_input.value = ""
        color_input.value = ""
        
        submit_btn.text = "ACTUALIZAR DATOS"
        cancel_btn.visible = True
        sku_input.disabled = True
        page.update()

    page.session.edit_product_func = load_product_for_edit

    if hasattr(page.session, "edit_request") and page.session.edit_request:
        load_product_for_edit(page.session.edit_request)
        page.session.edit_request = None

    return ft.Container(
        content=ft.Column(
            [
                ft.Row([title_text, cancel_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=FIELD_WIDTH),
                ft.Divider(height=1),
                provider_input,
                modelo_input,
                sku_input,
                brand_input,
                category_input,
                gender_input,
                tallas_input,
                color_input,
                stocks_input,
                condition_input,
                costo_input,
                tax_input,
                precio_input,
                ft.Divider(height=10, color="transparent"),
                ft.Column([photo_btn, photos_count_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                ft.Divider(height=10, color="transparent"),
                submit_btn
            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12
        ),
        padding=25,
        bgcolor=ft.Colors.WHITE,
        border_radius=15,
        border=ft.Border.all(1, ft.Colors.BLACK_12),
        width=350 
    )
