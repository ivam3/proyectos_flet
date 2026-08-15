import flet as ft

def sale_dialog(page: ft.Page, product, on_success):
    api = page.session.api
    
    # Determinamos si es móvil por el ancho de la página
    is_mobile = page.width < 600

    # --- CAMPOS ---
    available_colors = sorted(list(set(s['color'] for s in product['sizes'])))
    
    color_dd = ft.Dropdown(
        label="Color",
        options=[ft.dropdown.Option(c) for c in available_colors],
        value=available_colors[0] if available_colors else "N/A",
        width=300 if is_mobile else 200
    )

    size_dd = ft.Dropdown(
        label="Talla",
        width=300 if is_mobile else 120
    )

    def on_color_change(e):
        selected_color = color_dd.value
        sizes = sorted(list(set(s['size'] for s in product['sizes'] if s['color'] == selected_color)))
        size_dd.options = [ft.dropdown.Option(s) for s in sizes]
        size_dd.value = sizes[0] if sizes else None
        size_dd.update()

    color_dd.on_change = on_color_change

    qty_input = ft.TextField(
        label="Cantidad", 
        value="1", 
        width=300 if is_mobile else 100, 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    
    # Inicializar tallas para el primer color
    on_color_change(None)

    status_dd = ft.Dropdown(
        label="Tipo de Operación",
        options=[
            ft.dropdown.Option("COMPLETED", "Venta Directa"),
            ft.dropdown.Option("PRE-SALE", "Pre-venta / Apartado"),
        ],
        value="COMPLETED",
        width=300
    )

    sales_id_input = ft.TextField(
        label="ID de Venta / Pedido (Obligatorio)", 
        width=300, 
        keyboard_type=ft.KeyboardType.NUMBER
    )

    dist_dd = ft.Dropdown(
        label="Canal de Distribución",
        options=[
            ft.dropdown.Option("venta presencial"),
            ft.dropdown.Option("venta en linea"),
            ft.dropdown.Option("venta por redes sociales"),
            ft.dropdown.Option("venta telefonica"),
            ft.dropdown.Option("venta por catalogo"),
            ft.dropdown.Option("venta directa"),
        ],
        value="venta presencial",
        width=300
    )

    offer_type = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="PERCENT", label="%"),
            ft.Radio(value="FIXED", label="$")
        ]),
        value="PERCENT"
    )
    offer_value = ft.TextField(label="Descuento", value="0", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    
    customer_name = ft.TextField(label="Nombre del Cliente", width=300)
    customer_phone = ft.TextField(label="Teléfono del Cliente", width=300)
    comments_input = ft.TextField(label="Observaciones / Notas", multiline=True, max_lines=3, width=300)

    def show_alert(title, message, color=ft.Colors.RED):
        dlg_alert = ft.AlertDialog(
            title=ft.Text(title, color=color),
            content=ft.Text(message),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: [setattr(dlg_alert, "open", False), page.update()])]
        )
        page.overlay.append(dlg_alert)
        dlg_alert.open = True
        page.update()

    def on_confirm(e):
        if not sales_id_input.value:
            return show_alert("Requerido", "El ID de Venta es obligatorio")
        if not size_dd.value:
            return show_alert("Requerido", "Selecciona una talla")

        # 1. Encontrar la variante específica
        variant = next((s for s in product['sizes'] if s['color'] == color_dd.value and s['size'] == size_dd.value), None)
        if not variant:
            return show_alert("Error", "Combinación no disponible")

        # 2. Calcular precio con descuento
        base_price = product['price']
        off_val = float(offer_value.value or 0)
        final_p = base_price
        
        if offer_type.value == "PERCENT":
            final_p = base_price * (1 - (off_val / 100))
        else:
            final_p = base_price - off_val

        # 3. Datos del movimiento
        movement_data = {
            "size_id": variant['id'],
            "movement_type": "OUT",
            "quantity": int(qty_input.value),
            "description": f"{'Venta' if status_dd.value == 'COMPLETED' else 'Pre-venta'} de {product['model_name']}",
            "color": color_dd.value,
            "distribution_channel": dist_dd.value,
            "offer_type": offer_type.value,
            "offer_value": off_val,
            "final_price": final_p,
            "sales_id": sales_id_input.value,
            "customer_name": customer_name.value,
            "customer_phone": customer_phone.value,
            "comments": comments_input.value,
            "status": status_dd.value
        }

        res = api.create_movement(movement_data)
        if res["success"]:
            dlg.open = False
            page.update()
            on_success()
            show_alert("Éxito", "Operación registrada correctamente", ft.Colors.GREEN)
        else:
            show_alert("Error", f"No se pudo registrar: {res.get('error')}")

    # --- DISEÑO FINAL ---
    if is_mobile:
        layout = ft.Column(
            [
                ft.Text("Variante:", weight="bold"),
                color_dd, size_dd, qty_input,
                ft.Divider(),
                ft.Text("Operación:", weight="bold"),
                status_dd, sales_id_input, dist_dd,
                ft.Divider(),
                ft.Text("Descuento:", weight="bold"),
                ft.Row([offer_type, offer_value], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("Cliente:", weight="bold"),
                customer_name, customer_phone, comments_input,
            ],
            tight=True,
            scroll=ft.ScrollMode.ALWAYS,
            max_height=450,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    else:
        layout = ft.Column(
            [
                ft.Row([color_dd, size_dd, qty_input], spacing=10),
                ft.Row([status_dd, sales_id_input, dist_dd], spacing=10),
                ft.Row([ft.Text("Descuento:"), offer_type, offer_value], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([customer_name, customer_phone], spacing=10),
                comments_input,
            ],
            tight=True,
            width=650
        )

    dlg = ft.AlertDialog(
        title=ft.Text(f"Salida: {product['model_name']}", size=20, weight="bold"),
        content=layout,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: [setattr(dlg, "open", False), page.update()]),
            ft.ElevatedButton("Confirmar Operación", on_click=on_confirm, bgcolor=ft.Colors.ORANGE_700, color="white")
        ],
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()
