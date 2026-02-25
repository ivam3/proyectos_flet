# app/src/app_views/menu.py
import flet as ft
from config import IMAGES_URL
from database import obtener_menu, get_configuracion

def cargar_menu(page: ft.Page):
    """Carga y muestra los platillos del menú con pestañas por categoría."""
    
    user_cart = page.session.cart
    main_content = ft.Container(expand=True)
    
    # Estado del filtro actual
    current_category = None # None significa 'Todos'

    def update_menu_list(search_term="", category=None):
        nonlocal current_category
        current_category = category
        
        platillos_all = obtener_menu(solo_activos=True, search_term=search_term)
        
        # Filtrado por categoría
        if category:
            platillos = [p for p in platillos_all if p.get('categoria_id') == category]
        else:
            platillos = platillos_all

        platillos.sort(key=lambda x: x.get('descuento', 0) or 0, reverse=True)

        # Responsive: Ratio y Columnas
        if page.width < 600:
            current_ratio = 0.65  # Mucho más alto para móviles (evita encimado radicalmente)
            columns = 2
            img_height = 80       # Imagen más pequeña en móvil
        else:
            current_ratio = 0.8   # Ajustado para evitar superposición en Web/PC
            columns = 0           # Auto
            img_height = 110      # Imagen normal en web

        if not platillos:
            config = get_configuracion()
            horario = config['horario'] if config else "No disponible"
            main_content.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INFO_OUTLINED, size=40, color=ft.Colors.GREY_500),
                    ft.Text("Sin servicio", weight="bold", color=ft.Colors.BLACK),
                    ft.Text(horario, size=12, text_align="center", color=ft.Colors.BLACK),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0), expand=True
            )
        else:
            menu_grid = ft.GridView(
                expand=True,
                runs_count=columns,
                max_extent=250,
                child_aspect_ratio=current_ratio,
                spacing=10, run_spacing=10, padding=10
            )

            for platillo in platillos:
                pid = platillo['id']
                nombre = platillo['nombre']
                descripcion = platillo.get('descripcion', "")
                precio = platillo['precio']
                imagen = platillo.get('imagen')
                descuento = platillo.get('descuento', 0)
                is_configurable = platillo.get('is_configurable', 0)
                is_configurable_salsa = platillo.get('is_configurable_salsa', 0)
                piezas = platillo.get('piezas', 1)
                grupos_opciones_ids = platillo.get('grupos_opciones_ids', "[]")

                precio_final = precio * (1 - descuento / 100) if descuento > 0 else precio

                # --- LÓGICA DE ACCIONES (Añadir / Cantidad) ---
                def create_action_buttons(p_id, p_nombre, p_precio, p_img, p_is_conf, p_is_conf_salsa, p_pz, p_g_ids, container_ref):
                    qty = user_cart.get_item_quantity(p_id)
                    
                    if qty == 0:
                        # Botón Agregar inicial
                        return ft.IconButton(
                            icon=ft.Icons.ADD_SHOPPING_CART, 
                            icon_size=20,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, shape=ft.CircleBorder()),
                            on_click=lambda e: _on_add_first(e, p_id, p_nombre, p_precio, p_img, p_is_conf, p_is_conf_salsa, p_pz, p_g_ids, container_ref)
                        )
                    else:
                        # Selector de cantidad - 1 +
                        return ft.Container(
                            bgcolor=ft.Colors.ORANGE_100,
                            border_radius=20,
                            padding=ft.Padding.symmetric(horizontal=5),
                            content=ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.REMOVE, 
                                    icon_size=16, 
                                    icon_color=ft.Colors.ORANGE_900,
                                    on_click=lambda e: _on_change_qty(e, p_id, -1, container_ref)
                                ),
                                ft.Text(str(qty), weight="bold", size=14, color=ft.Colors.ORANGE_900),
                                ft.IconButton(
                                    icon=ft.Icons.ADD, 
                                    icon_size=16, 
                                    icon_color=ft.Colors.ORANGE_900,
                                    on_click=lambda e: _on_change_qty(e, p_id, 1, container_ref)
                                ),
                            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
                        )

                def _on_add_first(e, item_id, name, price, img, is_conf, is_conf_salsa, pz, g_ids, container_ref):
                    user_cart.add_item(item_id, name, price, img, is_configurable=is_conf, is_configurable_salsa=is_conf_salsa, piezas=pz, grupos_opciones_ids=g_ids)
                    container_ref.content = create_action_buttons(item_id, name, price, img, is_conf, is_conf_salsa, pz, g_ids, container_ref)
                    page.update()

                def _on_change_qty(e, item_id, delta, container_ref):
                    current_qty = user_cart.get_item_quantity(item_id)
                    new_qty = current_qty + delta
                    user_cart.update_quantity(item_id, new_qty)
                    
                    p = next((item for item in platillos if item['id'] == item_id), None)
                    if p:
                        container_ref.content = create_action_buttons(
                            item_id, p['nombre'], p['precio'], p.get('imagen'), 
                            p.get('is_configurable',0), p.get('is_configurable_salsa',0), 
                            p.get('piezas',1), p.get('grupos_opciones_ids',"[]"),
                            container_ref
                        )
                    page.update()

                p_display = ft.Column([
                    ft.Text(f"${precio:.0f}", size=10, color=ft.Colors.GREY, 
                            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH), 
                            visible=descuento > 0),
                    ft.Text(f"${precio_final:.0f}", weight="bold", size=14, color=ft.Colors.RED_700 if descuento > 0 else ft.Colors.ORANGE_800)
                ], spacing=0)

                # Lógica para determinar el origen de la imagen
                if imagen:
                    if imagen.startswith(("http://", "https://")):
                        img_src = imagen
                    elif "." in imagen and not imagen.startswith("/"):
                        img_src = f"{IMAGES_URL}/{imagen}"
                    else:
                        img_src = f"/{imagen}"
                else:
                    img_src = "/icon.png"

                # Contenedor para los botones de acción
                action_area = ft.Container()
                action_area.content = create_action_buttons(pid, nombre, precio_final, imagen, is_configurable, is_configurable_salsa, piezas, grupos_opciones_ids, action_area)

                menu_grid.controls.append(
                    ft.Card(
                        elevation=3,
                        content=ft.Container(
                            padding=8,
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                spacing=4,
                                controls=[
                                    ft.Container(
                                        content=ft.Stack([
                                            ft.Image(src=img_src, fit="cover", width=1000, height=img_height),
                                            ft.Container(
                                                content=ft.Text(f"-{descuento:.0f}%", color="white", size=9, weight="bold"),
                                                bgcolor=ft.Colors.RED, padding=4, border_radius=ft.BorderRadius.only(top_left=8, bottom_right=8),
                                                visible=descuento > 0
                                            )
                                        ]),
                                        height=img_height, border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                    ),
                                    ft.Text(nombre, weight=ft.FontWeight.BOLD, size=13, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.BLACK),
                                    ft.Text(descripcion or "", size=11, color=ft.Colors.GREY_800, max_lines=4, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Container(expand=True),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            p_display,
                                            action_area
                                        ]
                                    )
                                ]
                            ),
                        )
                    )
                )
            main_content.content = menu_grid
        page.update()

    def on_page_resize(e):
        update_menu_list(search_bar.value)

    page.on_resized = on_page_resize

    def handle_search_change(e):
        update_menu_list(e.control.value, current_category)

    search_bar = ft.TextField(
        label="Buscar...", prefix_icon=ft.Icons.SEARCH,
        on_change=handle_search_change, border_radius=20, height=40,
        text_size=14, content_padding=10, filled=True,
        text_style=ft.TextStyle(color=ft.Colors.BLACK),
        label_style=ft.TextStyle(color=ft.Colors.GREY_700)
    )

    # --- SISTEMA DE CATEGORÍAS (COMPATIBLE) ---
    categorias_row = ft.Row(scroll="auto", spacing=5)
    
    def on_category_click(category_name):
        update_menu_list(search_bar.value, category_name)
        refresh_categories_ui()

    def build_category_button(name, is_all=False):
        is_selected = (is_all and current_category is None) or (name == current_category)
        return ft.TextButton(
            content=ft.Text(name, color=ft.Colors.BROWN_700 if is_selected else ft.Colors.BLACK, 
                           weight="bold" if is_selected else "normal"),
            on_click=lambda _: on_category_click(None if is_all else name)
        )

    def refresh_categories_ui():
        categorias_row.controls.clear()
        categorias_row.controls.append(build_category_button("Todos", is_all=True))
        
        config = get_configuracion()
        if config and config.get("categorias_disponibles"):
            import json
            try:
                cats = json.loads(config["categorias_disponibles"])
                for c in cats:
                    categorias_row.controls.append(build_category_button(c))
            except:
                pass
        page.update()

    update_menu_list()
    refresh_categories_ui()

    return ft.Column(
        expand=True,
        spacing=0,
        controls=[
            ft.Container(content=search_bar, padding=ft.Padding.only(left=15, right=15, top=10, bottom=5)),
            ft.Container(content=categorias_row, padding=ft.Padding.only(left=15, right=15, bottom=5)),
            main_content
        ]
    )
